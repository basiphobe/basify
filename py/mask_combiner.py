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
                "masks": ("MASK", {
                    "tooltip": "Input masks to combine (can be a batch of masks)"
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
    
    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("combined_mask",)
    FUNCTION = "combine_masks"
    CATEGORY = "basify"
    
    def combine_masks(self, masks: Tensor, combine_mode: str) -> tuple[Tensor]:
        """Combine multiple masks into a single mask using the specified mode.
        
        Args:
            masks: Input mask tensor. Expected shapes:
                   - [batch, height, width] for batch of masks
                   - [height, width] for single mask
            combine_mode: Combination method - "union", "intersection", "average", "add", or "multiply"
            
        Returns:
            tuple: (combined_mask,) containing the combined mask as a tensor
        """
        try:
            # Ensure masks is a tensor
            if not isinstance(masks, type(torch.Tensor)):  # type: ignore[attr-defined]
                masks = torch.tensor(masks)  # type: ignore[attr-defined]
            
            # Handle different input shapes
            if len(masks.shape) == 2:
                # Single mask [height, width] - return as-is
                logger.info(f"[{loggerName}] Single mask provided, returning as-is")
                return (masks,)
            
            elif len(masks.shape) == 3:
                # Batch of masks [batch, height, width]
                batch_size = masks.shape[0]
                logger.info(f"[{loggerName}] Combining {batch_size} masks using mode: {combine_mode}")
                
                if batch_size == 1:
                    # Only one mask in batch - return it
                    result = masks[0]
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
                
                logger.info(
                    f"[{loggerName}] {Colors.GREEN}Successfully combined {batch_size} masks "
                    f"({masks.shape[1]}x{masks.shape[2]}) using {combine_mode}{Colors.ENDC}"
                )
                
                return (result,)
            
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
