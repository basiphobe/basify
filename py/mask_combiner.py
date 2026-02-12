import logging
from typing import Any, TYPE_CHECKING

try:
    import torch  # type: ignore[import]
except Exception:  # pragma: no cover - runtime import may not be available in static analysis
    torch = None

logger = logging.getLogger(__name__)

# Provide a lightweight fallback for `torch` attributes so static analysis
# and environments without torch don't error on attribute access.
if torch is None:  # pragma: no cover - fallback for editors/static analyzers
    class _TorchFallback:
        @staticmethod
        def clamp(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("torch not installed; clamp unavailable")
        
        @staticmethod
        def max(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("torch not installed; max unavailable")
        
        @staticmethod
        def min(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("torch not installed; min unavailable")
        
        @staticmethod
        def mean(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("torch not installed; mean unavailable")
        
        @staticmethod
        def sum(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("torch not installed; sum unavailable")

    torch = _TorchFallback()  # type: ignore

class Colors:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ENDC = '\033[0m'

loggerName = f"{Colors.BLUE}BASIFY MaskCombiner{Colors.ENDC}"


if TYPE_CHECKING:
    from torch import Tensor  # type: ignore
else:
    Tensor = Any  # fallback for static analysis/runtime absence


class MaskCombiner:
    """
    A ComfyUI node for combining multiple masks into a single mask.
    
    Features:
    - Accepts a batch of masks or list of mask tensors
    - Multiple combination modes: Union (Max), Intersection (Min), Average, Add, Multiply
    - Automatically handles different batch sizes
    - Clamps output values to valid mask range [0.0, 1.0]
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "masks": ("*", {
                    "tooltip": "Input masks to combine (accepts batched tensors, lists, or individual masks)"
                }),
                "combine_mode": (["union", "intersection", "average", "add", "multiply"], {
                    "default": "union",
                    "tooltip": "How to combine the masks:\n"
                               "- union: Take maximum value at each pixel (OR operation)\n"
                               "- intersection: Take minimum value at each pixel (AND operation)\n"
                               "- average: Average all mask values\n"
                               "- add: Sum all masks (clamped to [0,1])\n"
                               "- multiply: Multiply all masks together"
                }),
            }
        }
    
    INPUT_IS_LIST = True
    
    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("combined_mask",)
    FUNCTION = "combine_masks"
    CATEGORY = "basify"
    
    def combine_masks(self, masks: list[Tensor] | Tensor, combine_mode: list[str] | str) -> tuple[Tensor]:
        """Combine multiple masks into a single mask using the specified mode.
        
        Args:
            masks: Input masks as a list (when INPUT_IS_LIST=True) or single tensor.
                   When list: list of mask tensors (each [height, width] or [1, height, width])
                   When tensor: batched tensor [batch, height, width] or single [height, width]
            combine_mode: Combination method - "union", "intersection", "average", "add", or "multiply"
                         (will be a list with one item when INPUT_IS_LIST=True)
            
        Returns:
            tuple: (combined_mask,) containing the combined mask as a batched tensor [1, height, width]
        """
        try:
            # Extract combine_mode from list (INPUT_IS_LIST means it's always a list)
            if isinstance(combine_mode, list):
                combine_mode = combine_mode[0]
            
            # Collect and flatten all mask inputs
            all_masks = []
            if isinstance(masks, (list, tuple)):
                for m in masks:
                    if isinstance(m, (list, tuple)):
                        all_masks.extend(m)
                    else:
                        all_masks.append(m)
            else:
                all_masks = [masks]
            
            # Normalize each mask to 2D [H, W] before stacking
            normalized_masks = []
            for m in all_masks:
                if len(m.shape) == 3:
                    if m.shape[0] == 1:
                        normalized_masks.append(m.squeeze(0))
                    else:
                        # Multiple masks in batch, split them
                        for i in range(m.shape[0]):
                            normalized_masks.append(m[i])
                elif len(m.shape) == 2:
                    normalized_masks.append(m)
                else:
                    raise ValueError(f"Unexpected mask shape: {m.shape}")
            
            # Stack into batched tensor [N, H, W]
            masks = torch.stack(normalized_masks)  # type: ignore[attr-defined]
            
            # Handle single or multiple masks
            if len(masks.shape) == 2:
                # Single mask - add batch dimension and return
                return (masks.unsqueeze(0),)
            
            elif len(masks.shape) == 3:
                batch_size = masks.shape[0]
                
                if batch_size == 1:
                    # Only one mask - return with batch dimension
                    return (masks[0].unsqueeze(0),)
                else:
                    # Combine masks based on mode
                    if combine_mode == "union":
                        # Take maximum value at each pixel (OR operation)
                        result = torch.max(masks, dim=0)[0]  # type: ignore[attr-defined]
                    
                    elif combine_mode == "intersection":
                        # Take minimum value at each pixel (AND operation)
                        result = torch.min(masks, dim=0)[0]  # type: ignore[attr-defined]
                    
                    elif combine_mode == "average":
                        # Average all masks
                        result = torch.mean(masks, dim=0)  # type: ignore[attr-defined]
                    
                    elif combine_mode == "add":
                        # Sum all masks and clamp to [0, 1]
                        result = torch.sum(masks, dim=0)  # type: ignore[attr-defined]
                        result = torch.clamp(result, 0.0, 1.0)  # type: ignore[attr-defined]
                    
                    elif combine_mode == "multiply":
                        # Multiply all masks together
                        result = masks[0].clone()
                        for i in range(1, batch_size):
                            result = result * masks[i]
                    
                    else:
                        raise ValueError(f"Unknown combine_mode: {combine_mode}")
                
                # Add batch dimension to result
                output = result.unsqueeze(0)
                logger.info(
                    f"[{loggerName}] {Colors.GREEN}Combined {batch_size} masks "
                    f"({masks.shape[1]}x{masks.shape[2]}) using '{combine_mode}'{Colors.ENDC}"
                )
                
                return (output,)
            
            else:
                raise ValueError(
                    f"Unexpected mask shape: {masks.shape}. "
                    f"Expected [batch, height, width] or [height, width]"
                )
        
        except Exception as e:
            logger.error(f"[{loggerName}] Failed to combine masks: {e}")
            raise e


# Registration
NODE_CLASS_MAPPINGS = {
    "BasifyMaskCombiner": MaskCombiner
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyMaskCombiner": "Basify: Mask Combiner"
}
