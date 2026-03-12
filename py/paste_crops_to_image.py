import logging
import json
from typing import Any, TYPE_CHECKING

try:
    import torch  # type: ignore[import]
except Exception:  # pragma: no cover
    torch = None

logger = logging.getLogger(__name__)

# Provide a lightweight fallback for `torch` attributes so static analysis
# and environments without torch don't error on attribute access.
if torch is None:  # pragma: no cover
    class _TorchFallback:
        pass

    torch = _TorchFallback()  # type: ignore

class Colors:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ENDC = '\033[0m'

loggerName = f"{Colors.BLUE}BASIFY PasteCrops{Colors.ENDC}"


if TYPE_CHECKING:
    from torch import Tensor  # type: ignore
else:
    Tensor = Any


def detect_content_size(tensor: Tensor) -> tuple[int, int]:
    """
    Detect the real content size of a padded tensor by finding trailing all-zero rows/cols.
    
    Args:
        tensor: [H,W,C] or [H,W] tensor with padding on right/bottom
        
    Returns:
        (real_h, real_w) - dimensions of non-zero content
    """
    if len(tensor.shape) == 3:  # [H,W,C]
        # Check if any channel has non-zero values
        # Sum across channels to get [H,W]
        nonzero_map = tensor.abs().sum(dim=-1) > 0  # type: ignore[attr-defined]
    else:  # [H,W]
        nonzero_map = tensor.abs() > 0  # type: ignore[attr-defined]
    
    # Find last non-zero row
    row_has_content = nonzero_map.any(dim=1)  # type: ignore[attr-defined]
    if row_has_content.any():  # type: ignore[attr-defined]
        real_h = row_has_content.nonzero()[-1].item() + 1  # type: ignore[attr-defined]
    else:
        real_h = tensor.shape[0]
    
    # Find last non-zero col
    col_has_content = nonzero_map.any(dim=0)  # type: ignore[attr-defined]
    if col_has_content.any():  # type: ignore[attr-defined]
        real_w = col_has_content.nonzero()[-1].item() + 1  # type: ignore[attr-defined]
    else:
        real_w = tensor.shape[1]
    
    return (int(real_h), int(real_w))


def resize_tensor(tensor: Tensor, target_h: int, target_w: int, mode: str = "bicubic") -> Tensor:
    """
    Resize a [H,W,C] tensor to [target_h, target_w, C] using interpolation.
    
    Args:
        tensor: Input tensor [H,W,C]
        target_h: Target height
        target_w: Target width
        mode: Interpolation mode ("bilinear" or "bicubic")
        
    Returns:
        Resized tensor [target_h, target_w, C]
    """
    # Convert HWC to NCHW
    tensor_nchw = tensor.permute(2, 0, 1).unsqueeze(0)  # [1,C,H,W]  # type: ignore[attr-defined]
    
    # Resize
    resized = torch.nn.functional.interpolate(  # type: ignore[attr-defined]
        tensor_nchw,
        size=(target_h, target_w),
        mode=mode,
        align_corners=False if mode == "bicubic" else None
    )
    
    # Convert back to HWC
    result = resized.squeeze(0).permute(1, 2, 0)  # [H,W,C]  # type: ignore[attr-defined]
    
    return result


class BasifyPasteCropsToImage:
    """
    A ComfyUI node for pasting cropped (and potentially upscaled) images back onto a base image.
    
    Features:
    - Paste crops using metadata from BasifyCropFromBBoxes
    - Automatically detects and handles padding in crops
    - Supports resizing crops back to original size
    - Optional mask-based alpha blending
    - Clips out-of-bounds regions or raises error based on settings
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "base_image": ("IMAGE", {
                    "tooltip": "Base image to paste crops onto [B,H,W,C], typically B=1"
                }),
                "crops": ("IMAGE", {
                    "tooltip": "Batch of crops [N,pad_h,pad_w,C], top-left aligned with padding"
                }),
                "rects_json": ("STRING", {
                    "tooltip": "JSON array of crop rectangles from BasifyCropFromBBoxes"
                }),
                "mode": (["alpha", "replace"], {
                    "default": "alpha",
                    "tooltip": "Paste mode: 'alpha' uses masks for blending, 'replace' overwrites"
                }),
                "resize_to_rect": (["on", "off"], {
                    "default": "on",
                    "tooltip": "Resize crops to match original rect size before pasting"
                }),
                "interp": (["bicubic", "bilinear"], {
                    "default": "bicubic",
                    "tooltip": "Interpolation method for resizing"
                }),
                "clamp": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Clamp output values to [0,1]"
                }),
                "allow_oob_clip": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Clip out-of-bounds rects instead of raising error"
                }),
            },
            "optional": {
                "masks": ("MASK", {
                    "tooltip": "Optional masks [N,pad_h,pad_w] for alpha blending"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "paste"
    CATEGORY = "basify"
    
    def paste(
        self,
        base_image: Tensor,
        crops: Tensor,
        rects_json: str,
        mode: str = "alpha",
        resize_to_rect: str = "on",
        interp: str = "bicubic",
        clamp: bool = True,
        allow_oob_clip: bool = False,
        masks: Tensor | None = None
    ) -> tuple[Tensor]:
        """
        Paste crops back onto a base image using rect metadata.
        
        Args:
            base_image: Base image tensor [B,H,W,C]
            crops: Batch of cropped images [N,pad_h,pad_w,C]
            rects_json: JSON string with crop rectangle metadata
            mode: "alpha" for masked blending, "replace" for direct paste
            resize_to_rect: "on" to resize crops to rect size, "off" to use as-is
            interp: Interpolation mode for resizing
            clamp: Whether to clamp output to [0,1]
            allow_oob_clip: Whether to clip out-of-bounds regions
            masks: Optional masks for alpha blending [N,pad_h,pad_w]
            
        Returns:
            tuple: (modified_image,)
        """
        # Validate base_image format
        if len(base_image.shape) != 4:  # type: ignore[attr-defined]
            raise ValueError(
                f"Expected base_image with shape [B,H,W,C], got {base_image.shape}"  # type: ignore[attr-defined]
            )
        
        base_batch, base_h, base_w, base_c = base_image.shape  # type: ignore[attr-defined]
        
        if base_batch != 1:
            raise ValueError(
                f"BasifyPasteCropsToImage requires base_image batch_size=1, got {base_batch}"
            )
        
        # Validate crops format
        if len(crops.shape) != 4:  # type: ignore[attr-defined]
            raise ValueError(
                f"Expected crops with shape [N,pad_h,pad_w,C], got {crops.shape}"  # type: ignore[attr-defined]
            )
        
        num_crops, pad_h, pad_w, crop_c = crops.shape  # type: ignore[attr-defined]
        
        if crop_c != base_c:
            raise ValueError(
                f"Channel mismatch: base_image has {base_c} channels, crops have {crop_c}"
            )
        
        # Parse rects JSON
        if not rects_json or not rects_json.strip():
            raise ValueError(
                "rects_json is empty. Please connect the crop_rects output from BasifyCropFromBBoxes"
            )
        
        try:
            rects = json.loads(rects_json)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse rects_json: {e}\n"
                f"Expected JSON array from BasifyCropFromBBoxes, got: {rects_json[:100]}"
            )
        
        if not isinstance(rects, list):
            raise ValueError(f"rects_json must be a JSON array, got {type(rects)}")
        
        if len(rects) != num_crops:
            raise ValueError(
                f"Mismatch: {num_crops} crops but {len(rects)} rects in JSON"
            )
        
        # Validate masks if provided
        if masks is not None:
            if len(masks.shape) != 3:  # type: ignore[attr-defined]
                raise ValueError(
                    f"Expected masks with shape [N,pad_h,pad_w], got {masks.shape}"  # type: ignore[attr-defined]
                )
            
            num_masks, mask_h, mask_w = masks.shape  # type: ignore[attr-defined]
            
            if num_masks != num_crops:
                raise ValueError(
                    f"Mismatch: {num_crops} crops but {num_masks} masks"
                )
            
            if mask_h != pad_h or mask_w != pad_w:
                raise ValueError(
                    f"Mask dimensions [{mask_h},{mask_w}] don't match crop padding [{pad_h},{pad_w}]"
                )
        
        logger.info(
            f"[{loggerName}] Pasting {num_crops} crops onto base image {base_w}x{base_h}, "
            f"mode={mode}, resize_to_rect={resize_to_rect}"
        )
        
        # Clone base image to avoid modifying input
        output = base_image.clone()  # type: ignore[attr-defined]
        
        # Process each crop
        for i in range(num_crops):
            rect = rects[i]
            
            # Extract rect coordinates
            required_keys = ["x", "y", "w", "h"]
            for key in required_keys:
                if key not in rect:
                    raise ValueError(f"rect[{i}] missing required key '{key}'")
            
            x = int(rect["x"])
            y = int(rect["y"])
            w = int(rect["w"])
            h = int(rect["h"])
            
            # Validate dimensions
            if w < 1 or h < 1:
                raise ValueError(f"Invalid rect[{i}]: w={w}, h={h} must be >= 1")
            
            # Handle out-of-bounds
            if x < 0 or y < 0 or x + w > base_w or y + h > base_h:
                if not allow_oob_clip:
                    raise ValueError(
                        f"rect[{i}] out of bounds: [{x},{y},{w},{h}] exceeds image [{base_w},{base_h}]"
                    )
                
                # Clip rect to image bounds
                orig_x, orig_y, orig_w, orig_h = x, y, w, h
                x = max(0, x)
                y = max(0, y)
                w = min(w, base_w - x)
                h = min(h, base_h - y)
                
                # Calculate crop offset for clipped region
                crop_offset_x = x - orig_x
                crop_offset_y = y - orig_y
                
                logger.debug(
                    f"[{loggerName}] Clipped rect[{i}]: [{orig_x},{orig_y},{orig_w},{orig_h}] "
                    f"-> [{x},{y},{w},{h}], crop_offset=[{crop_offset_x},{crop_offset_y}]"
                )
            else:
                crop_offset_x = 0
                crop_offset_y = 0
            
            # Extract crop
            crop_i = crops[i]  # [pad_h, pad_w, C]
            
            # Determine crop processing based on resize_to_rect
            if resize_to_rect == "on":
                # Detect real content size (excluding padding)
                real_h, real_w = detect_content_size(crop_i)
                
                logger.debug(
                    f"[{loggerName}] Crop {i}: detected content size {real_w}x{real_h} "
                    f"in padded {pad_w}x{pad_h}"
                )
                
                # Extract real content
                content = crop_i[:real_h, :real_w, :]
                
                # Resize to target rect size (w, h)
                if real_h != h or real_w != w:
                    crop_roi = resize_tensor(content, h, w, mode=interp)
                    logger.debug(
                        f"[{loggerName}] Resized crop {i} from {real_w}x{real_h} to {w}x{h}"
                    )
                else:
                    crop_roi = content
            else:
                # Fast path: directly slice to rect size
                crop_roi = crop_i[:h, :w, :]
                logger.debug(
                    f"[{loggerName}] Crop {i}: using direct slice [:h, :w] = {w}x{h}"
                )
            
            # Apply crop offset if clipped
            if crop_offset_x > 0 or crop_offset_y > 0:
                crop_roi = crop_roi[crop_offset_y:, crop_offset_x:, :]
            
            # Process mask if provided
            if masks is not None and mode == "alpha":
                mask_i = masks[i]  # [pad_h, pad_w]
                
                # Process mask similarly to crop
                if resize_to_rect == "on":
                    real_h_mask, real_w_mask = detect_content_size(mask_i)
                    mask_content = mask_i[:real_h_mask, :real_w_mask]
                    
                    if real_h_mask != h or real_w_mask != w:
                        # Resize mask using bilinear interpolation
                        mask_resized = resize_tensor(
                            mask_content.unsqueeze(-1),  # [H,W,1]  # type: ignore[attr-defined]
                            h, w, mode="bilinear"
                        ).squeeze(-1)  # [H,W]  # type: ignore[attr-defined]
                        mask_roi = mask_resized
                    else:
                        mask_roi = mask_content
                else:
                    mask_roi = mask_i[:h, :w]
                
                # Apply mask offset if clipped
                if crop_offset_x > 0 or crop_offset_y > 0:
                    mask_roi = mask_roi[crop_offset_y:, crop_offset_x:]
                
                # Clamp mask to [0,1] and add channel dimension
                mask_roi = mask_roi.clamp(0, 1).unsqueeze(-1)  # [h,w,1]  # type: ignore[attr-defined]
                
                # Alpha blend
                base_roi = output[0, y:y+h, x:x+w, :]
                blended = base_roi * (1 - mask_roi) + crop_roi * mask_roi
            else:
                # Direct replace
                blended = crop_roi
            
            # Paste onto output
            output[0, y:y+h, x:x+w, :] = blended
            
            logger.debug(
                f"[{loggerName}] Pasted crop {i} at [{x},{y}] size {w}x{h}"
            )
        
        # Clamp output if requested
        if clamp:
            output = output.clamp(0, 1)  # type: ignore[attr-defined]
        
        logger.info(
            f"[{loggerName}] Successfully pasted {num_crops} crops"
        )
        
        return (output,)


# Export for ComfyUI
NODE_CLASS_MAPPINGS = {
    "BasifyPasteCropsToImage": BasifyPasteCropsToImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyPasteCropsToImage": "Basify - Paste Crops to Image",
}
