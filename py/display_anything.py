import json
import logging
from typing import Any
from comfy.comfy_types.node_typing import IO

logger = logging.getLogger(__name__)

class DisplayAnythingAsText:
    """ComfyUI node that displays any input value as text in a readonly textarea.
    
    This node accepts any type of input and attempts to convert it to a human-readable
    text representation. It's useful for debugging, inspecting data structures, and
    visualizing intermediate values in workflows.
    """
    
    # Maximum characters to display before truncation
    MAX_DISPLAY_LENGTH = 50000
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, Any]]:
        return {
            "required": {
                "value": (IO.ANY, {
                    "tooltip": "Any value to display as text. Supports primitives, collections, tensors, and objects."
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }
    
    RETURN_TYPES = (IO.ANY,)
    RETURN_NAMES = ("value",)
    FUNCTION = "display_value"
    CATEGORY = "basify"
    OUTPUT_NODE = True
    
    def display_value(self, value: Any, unique_id: str | None = None) -> dict[str, Any]:
        """Convert the input value to displayable text and pass it through.
        
        Args:
            value: Any input value to display
            unique_id: Node unique ID (hidden parameter)
            
        Returns:
            tuple: (original_value,) for passthrough and {"ui": {"text": [converted_text]}} for display
        """
        try:
            text = self._convert_to_text(value)
            
            # Truncate if too long
            if len(text) > self.MAX_DISPLAY_LENGTH:
                truncated_length = len(text) - self.MAX_DISPLAY_LENGTH
                text = text[:self.MAX_DISPLAY_LENGTH] + f"\n\n... [truncated {truncated_length:,} characters]"
            
            logger.debug(f"[BASIFY Display Anything] Converting value of type {type(value).__name__}, text length: {len(text)}")
            
            # Return both the passthrough value and UI data
            return {"ui": {"text": [text]}, "result": (value,)}
            
        except Exception as e:
            error_text = f"Error converting value to text: {type(e).__name__}: {str(e)}\n\nValue type: {type(value).__name__}"
            logger.error(f"[BASIFY Display Anything] {error_text}")
            return {"ui": {"text": [error_text]}, "result": (value,)}
    
    def _convert_to_text(self, value: Any) -> str:
        """Convert any value to a displayable text representation.
        
        Args:
            value: Any value to convert
            
        Returns:
            str: Human-readable text representation
        """
        # Handle None
        if value is None:
            return "None"
        
        # Handle basic types
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        
        # Handle bytes
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return f"<bytes: {len(value)} bytes, not UTF-8 decodable>\n{repr(value[:100])}{'...' if len(value) > 100 else ''}"
        
        # Handle torch tensors
        try:
            import torch
            if isinstance(value, torch.Tensor):
                return self._tensor_to_text(value)
        except ImportError:
            pass
        
        # Handle numpy arrays
        try:
            import numpy as np
            if isinstance(value, np.ndarray):
                return self._numpy_to_text(value)
        except ImportError:
            pass
        
        # Handle dictionaries
        if isinstance(value, dict):
            try:
                return json.dumps(value, indent=2, default=str, ensure_ascii=False)
            except Exception:
                return self._safe_repr(value)
        
        # Handle lists and tuples
        if isinstance(value, (list, tuple)):
            try:
                # Try JSON formatting for structured data
                return json.dumps(value, indent=2, default=str, ensure_ascii=False)
            except Exception:
                return self._safe_repr(value)
        
        # Handle sets
        if isinstance(value, set):
            return f"set({list(value)})"  # type: ignore[arg-type]
        
        # Try to get a readable string representation
        return self._safe_repr(value)
    
    def _tensor_to_text(self, tensor: Any) -> str:
        """Convert a PyTorch tensor to detailed text representation.
        
        Args:
            tensor: PyTorch tensor
            
        Returns:
            str: Detailed tensor information
        """
        import torch
        
        lines = [
            f"PyTorch Tensor",
            f"  Shape: {tuple(tensor.shape)}",  # type: ignore[arg-type]
            f"  Dtype: {tensor.dtype}",  # type: ignore[attr-defined]
            f"  Device: {tensor.device}",  # type: ignore[attr-defined]
            f"  Requires grad: {tensor.requires_grad}",  # type: ignore[attr-defined]
        ]
        
        # Add statistics for numeric tensors
        if tensor.dtype in (torch.float16, torch.float32, torch.float64, torch.bfloat16,  # type: ignore[attr-defined]
                           torch.int8, torch.int16, torch.int32, torch.int64,
                           torch.uint8):
            try:
                # Move to CPU for statistics if needed
                cpu_tensor = tensor.detach().cpu() if tensor.is_cuda else tensor.detach()  # type: ignore[attr-defined]
                
                lines.extend([
                    f"  Min: {cpu_tensor.min().item():.6f}",  # type: ignore[attr-defined]
                    f"  Max: {cpu_tensor.max().item():.6f}",  # type: ignore[attr-defined]
                    f"  Mean: {cpu_tensor.float().mean().item():.6f}",  # type: ignore[attr-defined]
                    f"  Std: {cpu_tensor.float().std().item():.6f}",  # type: ignore[attr-defined]
                ])
                
                # Show a sample of values for small tensors
                if tensor.numel() <= 100:  # type: ignore[attr-defined]
                    lines.append(f"\nValues:\n{cpu_tensor}")
                elif tensor.numel() <= 1000:  # type: ignore[attr-defined]
                    lines.append(f"\nFirst 100 values:\n{cpu_tensor.flatten()[:100]}")  # type: ignore[attr-defined]
                    
            except Exception as e:
                lines.append(f"  (Statistics unavailable: {e})")
        
        return "\n".join(lines)
    
    def _numpy_to_text(self, array: Any) -> str:
        """Convert a NumPy array to detailed text representation.
        
        Args:
            array: NumPy array
            
        Returns:
            str: Detailed array information
        """
        import numpy as np
        
        lines = [
            f"NumPy Array",
            f"  Shape: {array.shape}",  # type: ignore[attr-defined]
            f"  Dtype: {array.dtype}",  # type: ignore[attr-defined]
            f"  Size: {array.size} elements",  # type: ignore[attr-defined]
        ]
        
        # Add statistics for numeric arrays
        if np.issubdtype(array.dtype, np.number):
            try:
                lines.extend([
                    f"  Min: {np.min(array):.6f}",
                    f"  Max: {np.max(array):.6f}",
                    f"  Mean: {np.mean(array):.6f}",
                    f"  Std: {np.std(array):.6f}",
                ])
                
                # Show a sample of values for small arrays
                if array.size <= 100:
                    lines.append(f"\nValues:\n{array}")
                elif array.size <= 1000:
                    lines.append(f"\nFirst 100 values:\n{array.flatten()[:100]}")
                    
            except Exception as e:
                lines.append(f"  (Statistics unavailable: {e})")
        else:
            # For non-numeric arrays, show a sample
            if array.size <= 20:
                lines.append(f"\nValues:\n{array}")
        
        return "\n".join(lines)
    
    def _safe_repr(self, value: Any) -> str:
        """Safely get a string representation of any value.
        
        Args:
            value: Any value
            
        Returns:
            str: Safe string representation
        """
        try:
            # Try str() first
            result = str(value)
            if result and result != f"<{type(value).__name__} object at 0x" and len(result) < 1000:
                return f"Type: {type(value).__name__}\n\n{result}"
        except Exception:
            pass
        
        try:
            # Try repr() as fallback
            result = repr(value)
            if result and len(result) < 1000:
                return f"Type: {type(value).__name__}\n\n{result}"
        except Exception:
            pass
        
        # Last resort: just show the type and basic object info
        try:
            attrs = dir(value)
            public_attrs = [attr for attr in attrs if not attr.startswith('_')][:20]
            return f"Type: {type(value).__name__}\n\nPublic attributes: {', '.join(public_attrs)}"
        except Exception:
            return f"Type: {type(value).__name__}\n\n(Unable to display value)"


NODE_CLASS_MAPPINGS = {
    "BasifyDisplayAnythingAsText": DisplayAnythingAsText
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyDisplayAnythingAsText": "Basify: Display Anything as Text"
}
