import logging
import random
from typing import Any, TYPE_CHECKING

try:
    import torch  # type: ignore[import]
except Exception:  # pragma: no cover - runtime import may not be available in static analysis
    torch = None

try:
    from comfy.comfy_types.node_typing import IO  # type: ignore[import]
except Exception:  # pragma: no cover - comfy types unavailable in static analysis/runtime
    class IO:  # minimal fallback for static analysis and tests
        ANY = "ANY"

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

loggerName = f"{Colors.BLUE}BASIFY BatchSelector{Colors.ENDC}"


if TYPE_CHECKING:
    from torch import Tensor  # type: ignore
else:
    Tensor = Any  # fallback for static analysis/runtime absence


class BatchSelector:
    """
    A ComfyUI node for selecting a specific item from a batch.
    
    Features:
    - Accepts batches of images, masks, latents, or any batch data
    - Index-based selection with modulo cycling for loop-friendly iteration
    - UI-based selection modes (first, last, random, middle)
    - Safe bounds checking with helpful error messages
    - Output type automatically matches input type
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "batch": (IO.ANY, {
                    "tooltip": "Input batch to select from (IMAGE, MASK, LATENT, or other batch types)"
                }),
                "selection_mode": (["first", "last", "random", "middle"], {
                    "default": "first",
                    "tooltip": "How to select from batch when index is not connected"
                }),
            },
            "optional": {
                "index": ("INT", {
                    "default": 0,
                    "min": -10000,
                    "max": 10000,
                    "step": 1,
                    "tooltip": "Optional index input. When connected, uses modulo to cycle through batch.\n"
                               "Overrides selection_mode. Safe for loops - never crashes on out of range."
                }),
            }
        }
    
    RETURN_TYPES = (IO.ANY,)  # type: ignore[misc]
    RETURN_NAMES = ("output",)
    FUNCTION = "select_item"
    CATEGORY = "basify"
    
    def select_item(
        self,
        batch: Any,
        selection_mode: str = "first",
        index: int | None = None
    ) -> tuple[Any]:
        """Select a specific item from a batch.
        
        Args:
            batch: Input batch - can be IMAGE tensor, MASK tensor, LATENT dict, or any batch type
            selection_mode: How to select when index is not provided ("first", "last", "random", "middle")
            index: Optional index input. When provided, uses modulo to cycle through batch.
                   Overrides selection_mode.
            
        Returns:
            tuple: (selected_item,) - same type as the input batch
        """
        try:
            # Determine batch type and extract tensor
            batch_type: str
            data: dict[str, Tensor] | None = None
            tensor: Tensor
            
            if isinstance(batch, dict) and "samples" in batch:
                # LATENT type
                batch_type = "LATENT"
                data = batch
                tensor = data["samples"]
            else:
                # IMAGE or MASK type (both are tensors)
                tensor = batch  # type: ignore[assignment]
                # Determine if IMAGE (4D) or MASK (3D)
                if len(tensor.shape) == 4:  # type: ignore[attr-defined]
                    batch_type = "IMAGE"
                elif len(tensor.shape) == 3:  # type: ignore[attr-defined]
                    batch_type = "MASK"
                else:
                    raise ValueError(
                        f"Expected IMAGE [batch, height, width, channels] or "
                        f"MASK [batch, height, width], but got shape {tensor.shape}"  # type: ignore[attr-defined]
                    )
            
            batch_size = tensor.shape[0]  # type: ignore[attr-defined]
            
            # Safety check: handle empty batch
            if batch_size == 0:
                raise ValueError("Cannot select from an empty batch")
            
            # Determine selected index
            if index is not None:
                # Index provided - use modulo mode for loop-safe cycling
                selected_idx = int(index) % batch_size
                logger.info(
                    f"[{loggerName}] Using index mode: {index} % {batch_size} = {selected_idx}"
                )
            else:
                # No index - use selection_mode
                if selection_mode == "first":
                    selected_idx = 0
                elif selection_mode == "last":
                    selected_idx = batch_size - 1
                elif selection_mode == "middle":
                    selected_idx = batch_size // 2
                elif selection_mode == "random":
                    selected_idx = random.randint(0, batch_size - 1)
                else:
                    # Fallback to first
                    selected_idx = 0
                
                logger.info(
                    f"[{loggerName}] Using selection_mode '{selection_mode}': "
                    f"selected index {selected_idx} from batch of {batch_size}"
                )
            
            logger.info(
                f"[{loggerName}] Selecting {batch_type} at index {selected_idx} "
                f"from batch of {batch_size}"
            )
            
            # Select the item and prepare output based on type
            if batch_type == "LATENT":
                # For latents, create new dict with selected sample
                selected_latent = {
                    "samples": tensor[selected_idx].unsqueeze(0)  # type: ignore[index,attr-defined]
                }
                logger.info(
                    f"[{loggerName}] {Colors.GREEN}Successfully selected latent {selected_idx} "
                    f"with shape {selected_latent['samples'].shape}{Colors.ENDC}"  # type: ignore[attr-defined]
                )
                return (selected_latent,)
            
            else:
                # For IMAGE/MASK, select and expand dims to maintain batch dimension
                selected_tensor = tensor[selected_idx].unsqueeze(0)  # type: ignore[index,attr-defined]
                
                logger.info(
                    f"[{loggerName}] {Colors.GREEN}Successfully selected {batch_type} {selected_idx} "
                    f"with shape {selected_tensor.shape}{Colors.ENDC}"  # type: ignore[attr-defined]
                )
                
                return (selected_tensor,)  # type: ignore[return-value]
        
        except Exception as e:
            logger.error(f"[{loggerName}] Failed to select item: {e}")
            raise e


# Registration
NODE_CLASS_MAPPINGS = {
    "BasifyBatchSelector": BatchSelector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyBatchSelector": "Basify: Batch Selector"
}
