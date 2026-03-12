import logging
import json
from typing import Any, TYPE_CHECKING

try:
    import torch  # type: ignore[import]
except Exception:  # pragma: no cover - runtime import may not be available in static analysis
    torch = None

try:
    import numpy as np  # type: ignore[import]
except Exception:  # pragma: no cover
    np = None

logger = logging.getLogger(__name__)

# Provide a lightweight fallback for `torch` attributes so static analysis
# and environments without torch don't error on attribute access.
if torch is None:  # pragma: no cover - fallback for editors/static analyzers
    class _TorchFallback:
        pass

    torch = _TorchFallback()  # type: ignore

class Colors:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ENDC = '\033[0m'

loggerName = f"{Colors.BLUE}BASIFY CropFromBBoxes{Colors.ENDC}"


if TYPE_CHECKING:
    from torch import Tensor  # type: ignore
else:
    Tensor = Any  # fallback for static analysis/runtime absence


def normalize_bboxes(bboxes: Any) -> list[list[float]]:
    """
    Normalize bounding boxes from various input formats to a standard list of [x1, y1, x2, y2] floats.
    
    Accepts:
    - numpy/torch array shaped [N,4] or [1,N,4]
    - Python list of lists [[x1,y1,x2,y2], ...]
    - String containing JSON for the above list
    
    Returns:
        list of [x1, y1, x2, y2] as floats
        
    Raises:
        ValueError: If input format is invalid or cannot be parsed
    """
    # Handle string input (JSON)
    if isinstance(bboxes, str):
        try:
            bboxes = json.loads(bboxes)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse bboxes JSON string: {e}")
    
    # Handle torch tensor
    if torch is not None and isinstance(bboxes, torch.Tensor):  # type: ignore[attr-defined]
        bboxes = bboxes.detach().cpu().numpy()
    
    # Handle numpy array
    if np is not None and isinstance(bboxes, np.ndarray):
        # Reshape [1,N,4] to [N,4] if needed
        if bboxes.ndim == 3 and bboxes.shape[0] == 1:
            bboxes = bboxes[0]
        
        if bboxes.ndim != 2 or bboxes.shape[1] != 4:
            raise ValueError(
                f"Expected bboxes array of shape [N,4] or [1,N,4], got {bboxes.shape}"
            )
        
        # Convert to list
        bboxes = bboxes.tolist()
    
    # Validate it's a list
    if not isinstance(bboxes, list):
        raise ValueError(
            f"Bboxes must be a list, numpy array, torch tensor, or JSON string, got {type(bboxes)}"
        )
    
    if len(bboxes) == 0:
        raise ValueError("Bboxes list cannot be empty")
    
    # Handle nested list structure [1, N, 4] - unwrap first dimension
    # Check if first element is itself a list/array of bboxes
    if len(bboxes) == 1 and (isinstance(bboxes[0], (list, tuple)) or (np is not None and isinstance(bboxes[0], np.ndarray))):
        first_elem = bboxes[0]
        
        # Convert numpy array to list if needed
        if np is not None and isinstance(first_elem, np.ndarray):
            first_elem = first_elem.tolist()
        
        # Check if first_elem looks like it contains multiple bboxes
        if hasattr(first_elem, '__len__') and len(first_elem) > 0:
            # Check if first_elem[0] has 4 elements (looks like a bbox)
            if isinstance(first_elem[0], (list, tuple)):
                if len(first_elem[0]) == 4:
                    # This is [1, N, 4] structure, unwrap it
                    bboxes = first_elem
    
    # Validate each bbox
    result: list[list[float]] = []
    for i, bbox in enumerate(bboxes):
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError(
                f"Each bbox must be a list/tuple of 4 numbers [x1,y1,x2,y2], "
                f"but bbox[{i}] is {bbox}"
            )
        
        try:
            x1, y1, x2, y2 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to convert bbox[{i}] to floats: {e}")
        
        # Validate coordinates
        if x2 <= x1:
            raise ValueError(f"Invalid bbox[{i}]: x2 ({x2}) must be > x1 ({x1})")
        if y2 <= y1:
            raise ValueError(f"Invalid bbox[{i}]: y2 ({y2}) must be > y1 ({y1})")
        
        result.append([x1, y1, x2, y2])
    
    return result


class BasifyCropFromBBoxes:
    """
    A ComfyUI node for cropping images based on bounding boxes.
    
    Features:
    - Takes an image and a collection of bounding boxes
    - Crops each bbox region with optional padding
    - Returns a batch of cropped images and metadata
    - Supports clamping to image boundaries and minimum size constraints
    - Pads all crops to the same size for batch consistency
    
    Example bbox input and calculation:
        Input bbox: [100, 200, 300, 400]  # x1, y1, x2, y2
        With pad_percent=0.35:
            w = 200, h = 200
            w2 = 200 * 1.35 = 270, h2 = 200 * 1.35 = 270
            cx = 200, cy = 300
            crop_x = 200 - 135 = 65
            crop_y = 300 - 135 = 165
            Result: Crop at (65, 165) with size (270, 270)
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "Input image tensor [B,H,W,C] in ComfyUI format"
                }),
                "bboxes": ("*", {
                    "tooltip": "Bounding boxes as array [N,4] or list [[x1,y1,x2,y2],...] or JSON string"
                }),
                "pad_percent": ("FLOAT", {
                    "default": 0.35,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "tooltip": "Padding to add around each bbox as a percentage of its size"
                }),
                "clamp_to_image": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Clamp crop regions to stay within image boundaries"
                }),
                "round_to_int": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Round crop coordinates to integers"
                }),
                "min_size": ("INT", {
                    "default": 16,
                    "min": 1,
                    "max": 4096,
                    "step": 1,
                    "tooltip": "Minimum allowed crop width/height after clamping"
                }),
            },
            "optional": {
                "max_crops": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1000,
                    "step": 1,
                    "tooltip": "Maximum number of crops to process (0 = no limit)"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("crops", "crop_rects")
    FUNCTION = "crop_from_bboxes"
    CATEGORY = "basify"
    
    def crop_from_bboxes(
        self,
        image: Tensor,
        bboxes: Any,
        pad_percent: float = 0.35,
        clamp_to_image: bool = True,
        round_to_int: bool = True,
        min_size: int = 16,
        max_crops: int = 0
    ) -> tuple[Tensor, str]:
        """
        Crop images based on bounding boxes.
        
        Args:
            image: Input image tensor [B,H,W,C] in ComfyUI format (torch, float, 0..1)
            bboxes: Bounding boxes in [x1,y1,x2,y2] format
            pad_percent: Padding to add around each bbox (0.0 to 1.0)
            clamp_to_image: Whether to clamp crop regions to image boundaries
            round_to_int: Whether to round coordinates to integers
            min_size: Minimum crop dimension after clamping
            max_crops: Maximum number of crops (0 = no limit)
            
        Returns:
            tuple: (cropped_images, crop_metadata_json)
                - cropped_images: Tensor [N,H,W,C] with all crops padded to max size
                - crop_metadata_json: JSON string with crop rectangle metadata
        """
        # Validate image format
        if len(image.shape) != 4:  # type: ignore[attr-defined]
            raise ValueError(
                f"Expected IMAGE tensor with shape [B,H,W,C], got shape {image.shape}"  # type: ignore[attr-defined]
            )
        
        batch_size, img_height, img_width, channels = image.shape  # type: ignore[attr-defined]
        
        # We only support single-image input (batch_size=1)
        # Multiple images with same bboxes could be ambiguous
        if batch_size != 1:
            raise ValueError(
                f"BasifyCropFromBBoxes currently only supports single images (batch_size=1), "
                f"but got batch_size={batch_size}. Process images individually."
            )
        
        # Normalize bboxes to standard format
        normalized_bboxes = normalize_bboxes(bboxes)
        num_bboxes = len(normalized_bboxes)
        
        # Apply max_crops limit
        if max_crops > 0 and num_bboxes > max_crops:
            logger.info(
                f"[{loggerName}] Limiting crops from {num_bboxes} to {max_crops}"
            )
            normalized_bboxes = normalized_bboxes[:max_crops]
            num_bboxes = max_crops
        
        logger.debug(
            f"[{loggerName}] Processing {num_bboxes} bboxes from image of size "
            f"({img_width}x{img_height}), pad_percent={pad_percent}"
        )
        
        # Calculate crop rectangles
        crop_rects: list[dict[str, float]] = []
        crop_tensors: list[Tensor] = []
        
        for i, bbox in enumerate(normalized_bboxes):
            x1, y1, x2, y2 = bbox
            
            # Calculate original bbox dimensions
            w = x2 - x1
            h = y2 - y1
            
            # Apply padding
            w2 = w * (1.0 + pad_percent)
            h2 = h * (1.0 + pad_percent)
            
            # Calculate center and new top-left
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            x = cx - w2 / 2.0
            y = cy - h2 / 2.0
            
            # Round to int if requested
            if round_to_int:
                x = float(int(x))
                y = float(int(y))
                w2 = float(round(w2))
                h2 = float(round(h2))
            
            # Clamp to image boundaries if requested
            if clamp_to_image:
                # Ensure we don't go outside image
                x = max(0.0, x)
                y = max(0.0, y)
                
                # Adjust width/height to fit within image
                if x + w2 > img_width:
                    w2 = float(img_width) - x
                if y + h2 > img_height:
                    h2 = float(img_height) - y
                
                # Enforce minimum size
                w2 = max(float(min_size), w2)
                h2 = max(float(min_size), h2)
                
                # If enforcing min_size pushed us outside, shift back
                if x + w2 > img_width:
                    x = max(0.0, float(img_width) - w2)
                if y + h2 > img_height:
                    y = max(0.0, float(img_height) - h2)
            
            # Compute final coordinates for metadata
            final_x1 = x
            final_y1 = y
            final_x2 = x + w2
            final_y2 = y + h2
            
            # Store metadata
            crop_rect = {
                "x": x,
                "y": y,
                "w": w2,
                "h": h2,
                "x1": final_x1,
                "y1": final_y1,
                "x2": final_x2,
                "y2": final_y2,
                "cx": cx,
                "cy": cy,
                "pad_percent": pad_percent,
            }
            crop_rects.append(crop_rect)
            
            # Perform the crop (convert to pixel coordinates)
            # ComfyUI images are [B,H,W,C], need to index as [batch, y:y+h, x:x+w, :]
            crop_x = int(x)
            crop_y = int(y)
            crop_w = int(w2)
            crop_h = int(h2)
            
            # Ensure we don't exceed image bounds
            crop_x = max(0, min(crop_x, img_width - 1))
            crop_y = max(0, min(crop_y, img_height - 1))
            crop_w = min(crop_w, img_width - crop_x)
            crop_h = min(crop_h, img_height - crop_y)
            
            # Extract crop from first image in batch
            crop = image[0, crop_y:crop_y+crop_h, crop_x:crop_x+crop_w, :]
            crop_tensors.append(crop)
            
            logger.debug(
                f"[{loggerName}] Crop {i}: bbox=[{x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f}] "
                f"-> rect=[{crop_x},{crop_y},{crop_w},{crop_h}] "
                f"actual_shape={crop.shape}"  # type: ignore[attr-defined]
            )
        
        # Pad all crops to the same size (max dimensions in the batch)
        max_h = max(crop.shape[0] for crop in crop_tensors)  # type: ignore[attr-defined]
        max_w = max(crop.shape[1] for crop in crop_tensors)  # type: ignore[attr-defined]
        
        logger.debug(
            f"[{loggerName}] Padding all crops to max size: {max_w}x{max_h}"
        )
        
        padded_crops: list[Tensor] = []
        for crop in crop_tensors:
            h, w = crop.shape[0], crop.shape[1]  # type: ignore[attr-defined]
            
            if h == max_h and w == max_w:
                # No padding needed
                padded_crops.append(crop)
            else:
                # Pad to max size (pad on right and bottom)
                pad_h = max_h - h
                pad_w = max_w - w
                
                # torch.nn.functional.pad expects (left, right, top, bottom) for 2D
                # But our tensor is [H,W,C], so we need (left, right, top, bottom, front, back)
                # Actually for [H,W,C]: (C_left, C_right, W_left, W_right, H_top, H_bottom)
                # Simpler: just use zeros and concatenate
                padded = torch.nn.functional.pad(  # type: ignore[attr-defined]
                    crop,
                    (0, 0, 0, pad_w, 0, pad_h),  # pad width on right, height on bottom
                    mode='constant',
                    value=0
                )
                padded_crops.append(padded)
        
        # Stack into batch
        result_batch = torch.stack(padded_crops, dim=0)  # type: ignore[attr-defined]
        
        # Convert metadata to JSON
        crop_rects_json = json.dumps(crop_rects, indent=2)
        
        logger.info(
            f"[{loggerName}] Created {len(padded_crops)} crops of size {max_w}x{max_h}"
        )
        
        return (result_batch, crop_rects_json)


# Export for ComfyUI
NODE_CLASS_MAPPINGS = {
    "BasifyCropFromBBoxes": BasifyCropFromBBoxes,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyCropFromBBoxes": "Basify: Crop from BBoxes",
}
