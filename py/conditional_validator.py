import logging
from typing import Any

try:
    from comfy.comfy_types.node_typing import IO  # type: ignore[import]
except Exception:  # pragma: no cover - comfy types unavailable in static analysis/runtime
    class IO:  # minimal fallback for static analysis and tests
        ANY = "ANY"

logger = logging.getLogger(__name__)


class ConditionalValidator:
    """ComfyUI node that validates a condition and passes through a value or stops execution.
    
    This node checks a boolean condition. If true, it passes through the input value.
    If false, it raises an error to stop the workflow execution.
    
    Use case: Stop processing when there's nothing more to process or when a 
    validation condition fails.
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, Any]]:
        return {
            "required": {
                "condition": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Boolean condition to check. If False, workflow execution stops."
                }),
                "value": (IO.ANY, {
                    "tooltip": "Any value to pass through when condition is True."
                }),
            },
            "optional": {
                "error_message": ("STRING", {
                    "default": "Validation failed: condition is False",
                    "multiline": True,
                    "tooltip": "Custom error message to display when condition is False."
                }),
            }
        }
    
    RETURN_TYPES = (IO.ANY,)  # type: ignore[misc]
    RETURN_NAMES = ("value",)
    FUNCTION = "validate_and_pass"
    CATEGORY = "basify"
    
    def validate_and_pass(self, condition: bool, value: Any, error_message: str = "Validation failed: condition is False") -> tuple[Any]:
        """Validate the condition and pass through the value or raise an error.
        
        Args:
            condition: Boolean condition to check
            value: Any value to pass through
            error_message: Custom error message for when condition is False
            
        Returns:
            tuple: (value,) when condition is True
            
        Raises:
            ValueError: When condition is False
        """
        if not condition:
            logger.error(f"[BASIFY Conditional Validator] {error_message}")
            raise ValueError(error_message)
        
        logger.debug(f"[BASIFY Conditional Validator] Condition passed, passing through value of type {type(value).__name__}")
        return (value,)


NODE_CLASS_MAPPINGS = {
    "BasifyConditionalValidator": ConditionalValidator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyConditionalValidator": "Basify: Conditional Validator",
}
