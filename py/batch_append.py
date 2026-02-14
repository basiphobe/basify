import logging
from typing import Any

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

class Colors:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ENDC = '\033[0m'

loggerName = f"{Colors.BLUE}BASIFY BatchAppend{Colors.ENDC}"

# Sentinel value to detect when batch input is not connected
_UNCONNECTED = object()


class BatchAppend:
    """
    A ComfyUI node for appending an item to a batch or collection.
    
    Features:
    - Accepts any type of batch/collection (list, tensor batch, etc.)
    - Accepts any type of item to append
    - Returns the batch with the item appended
    - Automatically handles different collection types (lists, tensors)
    - Maintains internal collection when no batch input is connected
    - Resets internal collection when batch is connected or item type changes
    """
    
    def __init__(self) -> None:
        """Initialize the node with internal state for collection accumulation."""
        self._internal_collection: Any = None
        self._last_item_type: type | None = None
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "item": (IO.ANY, {
                    "tooltip": "The item to append to the batch or internal collection"
                }),
            },
            "optional": {
                "batch": (IO.ANY, {
                    "tooltip": "Optional batch to append to. If not connected, uses internal collection."
                }),
            }
        }
    
    RETURN_TYPES = (IO.ANY,)
    RETURN_NAMES = ("batch",)
    FUNCTION = "append_to_batch"
    CATEGORY = "basify"
    
    def append_to_batch(self, item: Any, batch: Any = _UNCONNECTED) -> tuple[Any]:
        """Append an item to a batch or internal collection.
        
        Args:
            item: The item to append to the batch. Can be any type
            batch: Optional batch or collection to append to. If not connected, uses internal collection.
                   If connected but None, creates new collection.
            
        Returns:
            tuple: (batch_with_item,) containing the batch with the item appended
        """
        try:
            # Get current item type for type change detection
            current_item_type = type(item)
            
            # Detect item type changes and reset internal collection if changed
            if self._last_item_type is not None and current_item_type != self._last_item_type:
                logger.info(
                    f"[{loggerName}] {Colors.GREEN}Item type changed "
                    f"({self._last_item_type.__name__} → {current_item_type.__name__}), "
                    f"resetting internal collection{Colors.ENDC}"
                )
                self._internal_collection = None
            
            self._last_item_type = current_item_type
            
            # Case 1: Batch input is not connected - use internal accumulating collection
            if batch is _UNCONNECTED:
                # Initialize or append to internal collection
                if self._internal_collection is None:
                    # Create new collection based on item type
                    self._internal_collection = self._create_collection_for_item(item)
                    logger.info(
                        f"[{loggerName}] {Colors.GREEN}Created internal collection "
                        f"(type: {type(self._internal_collection).__name__}){Colors.ENDC}"
                    )
                else:
                    # Append to existing internal collection
                    self._internal_collection = self._append_to_collection(self._internal_collection, item)
                    logger.info(
                        f"[{loggerName}] {Colors.GREEN}Appended to internal collection "
                        f"(size: {self._get_collection_size(self._internal_collection)}){Colors.ENDC}"
                    )
                
                return (self._internal_collection,)
            
            # Case 2: Batch input is connected but is None - create new collection
            elif batch is None:
                # Reset internal collection since external batch is connected
                self._internal_collection = None
                
                # Create a new collection with just this item
                result = self._create_collection_for_item(item)
                logger.info(
                    f"[{loggerName}] {Colors.GREEN}Created new collection from None batch "
                    f"(type: {type(result).__name__}){Colors.ENDC}"
                )
                return (result,)
            
            # Case 3: Batch input has a value - append to it
            else:
                # Reset internal collection since external batch is connected
                self._internal_collection = None
                
                # Use the provided batch with original append logic
                result = self._append_to_external_batch(batch, item)
                return (result,)
        
        except Exception as e:
            logger.error(f"[{loggerName}] Failed to append item to batch: {e}")
            raise e
    
    def _create_collection_for_item(self, item: Any) -> Any:
        """Create a new collection containing the item.
        
        Args:
            item: The first item for the collection
            
        Returns:
            A new collection containing the item
        """
        # For tensors, add batch dimension
        if torch is not None and isinstance(item, torch.Tensor):
            if len(item.shape) > 0 and item.shape[0] != 1:
                # Item is already batched or needs batch dimension
                return item.unsqueeze(0) if item.dim() > 0 else item
            return item.unsqueeze(0)
        
        # For dicts with samples (latent format), wrap in single-item batch
        if isinstance(item, dict) and 'samples' in item:
            return item
        
        # Default: create a list
        return [item]
    
    def _append_to_collection(self, collection: Any, item: Any) -> Any:
        """Append an item to a collection.
        
        Args:
            collection: The existing collection
            item: The item to append
            
        Returns:
            The collection with the item appended
        """
        # Handle lists
        if isinstance(collection, (list, tuple)):
            return list(collection) + [item]
        
        # Handle torch tensors
        if torch is not None and isinstance(collection, torch.Tensor):
            if isinstance(item, torch.Tensor):
                # Ensure item has batch dimension
                if len(item.shape) == len(collection.shape) - 1:
                    item = item.unsqueeze(0)
                return torch.cat([collection, item], dim=0)
            else:
                # Item is not a tensor, convert to list
                return [collection, item]
        
        # Handle dicts with samples
        if isinstance(collection, dict) and 'samples' in collection:
            if isinstance(item, dict) and 'samples' in item:
                if torch is not None:
                    combined_samples = torch.cat([collection['samples'], item['samples']], dim=0)
                    return {'samples': combined_samples}
            return [collection, item]
        
        # Default: convert to list
        return [collection, item]
    
    def _get_collection_size(self, collection: Any) -> int:
        """Get the size of a collection.
        
        Args:
            collection: The collection to measure
            
        Returns:
            Size of the collection
        """
        if isinstance(collection, (list, tuple)):
            return len(collection)
        if torch is not None and isinstance(collection, torch.Tensor):
            return collection.shape[0]
        if isinstance(collection, dict) and 'samples' in collection:
            if torch is not None and isinstance(collection['samples'], torch.Tensor):
                return collection['samples'].shape[0]
        return 1
    
    def _append_to_external_batch(self, batch: Any, item: Any) -> Any:
        """Append an item to an external batch (original logic).
        
        Args:
            batch: The batch to append to
            item: The item to append
            
        Returns:
            The batch with item appended
        """
        # Case 1: Batch is a list or tuple
        if isinstance(batch, (list, tuple)):
            result = list(batch) + [item]
            logger.info(
                f"[{loggerName}] {Colors.GREEN}Appended item to list batch "
                f"(size: {len(batch)} → {len(result)}){Colors.ENDC}"
            )
            return result
        
        # Case 2: Batch is a torch tensor
        if torch is not None and isinstance(batch, torch.Tensor):
            # Check if item is also a tensor
            if isinstance(item, torch.Tensor):
                # Ensure item has batch dimension
                if len(item.shape) == len(batch.shape) - 1:
                    # Add batch dimension to item
                    item = item.unsqueeze(0)
                elif len(item.shape) == len(batch.shape) and item.shape[0] != 1:
                    # Item already has batch dimension but it's not 1
                    # This is fine, we'll concatenate
                    pass
                elif len(item.shape) != len(batch.shape):
                    raise ValueError(
                        f"Cannot append tensor with shape {item.shape} to batch with shape {batch.shape}. "
                        f"Shapes must be compatible for concatenation."
                    )
                
                # Concatenate along batch dimension (dim=0)
                result = torch.cat([batch, item], dim=0)
                logger.info(
                    f"[{loggerName}] {Colors.GREEN}Appended tensor to batch "
                    f"(batch size: {batch.shape[0]} → {result.shape[0]}){Colors.ENDC}"
                )
                return result
            else:
                # Item is not a tensor, convert batch to list and append
                result = [batch, item]
                logger.info(
                    f"[{loggerName}] {Colors.GREEN}Converted tensor batch to list and appended item{Colors.ENDC}"
                )
                return result
        
        # Case 3: Batch is a dict (e.g., latent format with 'samples' key)
        if isinstance(batch, dict) and 'samples' in batch:
            # Check if item is also a dict with 'samples'
            if isinstance(item, dict) and 'samples' in item:
                batch_samples = batch['samples']
                item_samples = item['samples']
                
                if torch is not None and isinstance(batch_samples, torch.Tensor) and isinstance(item_samples, torch.Tensor):
                    # Concatenate the sample tensors
                    combined_samples = torch.cat([batch_samples, item_samples], dim=0)
                    result = {'samples': combined_samples}
                    logger.info(
                        f"[{loggerName}] {Colors.GREEN}Appended latent samples "
                        f"(batch size: {batch_samples.shape[0]} → {combined_samples.shape[0]}){Colors.ENDC}"
                    )
                    return result
                else:
                    # Samples are not tensors, create list
                    result = [batch, item]
                    logger.info(
                        f"[{loggerName}] {Colors.GREEN}Converted dict batches to list{Colors.ENDC}"
                    )
                    return result
            else:
                # Item is not a dict with samples, create list
                result = [batch, item]
                logger.info(
                    f"[{loggerName}] {Colors.GREEN}Created list with dict batch and item{Colors.ENDC}"
                )
                return result
        
        # Case 4: Unknown type - convert to list and append
        result = [batch, item]
        logger.info(
            f"[{loggerName}] {Colors.GREEN}Converted batch to list and appended item "
            f"(batch type: {type(batch).__name__}){Colors.ENDC}"
        )
        return result


# Registration
NODE_CLASS_MAPPINGS = {
    "BasifyBatchAppend": BatchAppend
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyBatchAppend": "Basify: Batch Append"
}
