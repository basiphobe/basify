import logging
from typing import Any

try:
    from comfy.comfy_types.node_typing import IO  # type: ignore[import]
except Exception:  # pragma: no cover - comfy types unavailable in static analysis/runtime
    class IO:  # minimal fallback for static analysis and tests
        ANY = "ANY"

logger = logging.getLogger(__name__)


class LazyConditionalSwitch:
    """ComfyUI node that implements lazy conditional branching.
    
    This node evaluates only the selected branch based on a boolean condition,
    avoiding expensive computations on the unselected branch. This is critical
    for workflows where one branch may trigger heavy GPU operations (e.g., SAM
    segmentation) that should be bypassed when not needed.
    
    Only the input corresponding to the condition value is evaluated - the other
    remains completely unevaluated, preventing any upstream nodes from executing.
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, Any]]:
        return {
            "required": {
                "condition": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Boolean condition. If True, evaluates and returns true_value. If False, evaluates and returns false_value."
                }),
                "true_value": (IO.ANY, {
                    "lazy": True,
                    "tooltip": "Value to evaluate and return when condition is True. Not evaluated when condition is False."
                }),
                "false_value": (IO.ANY, {
                    "lazy": True,
                    "tooltip": "Value to evaluate and return when condition is False. Not evaluated when condition is True."
                }),
            }
        }
    
    RETURN_TYPES = (IO.ANY,)  # type: ignore[misc]
    RETURN_NAMES = ("value",)
    FUNCTION = "switch"
    CATEGORY = "basify"
    
    def check_lazy_status(self, condition: bool, true_value: Any = None, false_value: Any = None) -> list[str]:
        """Determine which inputs need to be evaluated based on the condition.
        
        This method is called by ComfyUI's lazy evaluation system before executing
        the main function. It returns a list of input names that need to be evaluated.
        
        Connected but unevaluated lazy inputs are passed as None. We check for None
        to ensure we only request evaluation when needed.
        
        Args:
            condition: The boolean condition value (always evaluated first)
            true_value: None if not yet evaluated, otherwise the evaluated value
            false_value: None if not yet evaluated, otherwise the evaluated value
            
        Returns:
            list[str]: Names of inputs that need to be evaluated
        """
        # Defensive: convert to bool in case condition is int/float (0/1) from comparison nodes
        cond = bool(condition)
        
        # Only request evaluation if the selected input hasn't been evaluated yet (is None)
        if cond and true_value is None:
            logger.debug("[BASIFY Lazy Conditional Switch] Condition is True, evaluating true_value")
            return ["true_value"]
        if (not cond) and false_value is None:
            logger.debug("[BASIFY Lazy Conditional Switch] Condition is False, evaluating false_value")
            return ["false_value"]
        
        # Input already evaluated or not needed
        return []
    
    def switch(self, condition: bool, true_value: Any = None, false_value: Any = None) -> tuple[Any]:
        """Execute the conditional switch and return the selected value.
        
        This function is only called after check_lazy_status has determined which
        inputs to evaluate. Only the selected input will be provided; the other
        will remain None.
        
        Args:
            condition: The boolean condition value
            true_value: Value to return when condition is True (None if not evaluated)
            false_value: Value to return when condition is False (None if not evaluated)
            
        Returns:
            tuple: (selected_value,)
        """
        # Defensive: convert to bool in case condition is int/float (0/1) from comparison nodes
        cond = bool(condition)
        
        if cond:
            if true_value is None:
                raise RuntimeError("true_value was not evaluated (lazy gate failed)")
            logger.debug(f"[BASIFY Lazy Conditional Switch] Returning true_value of type {type(true_value).__name__}")
            return (true_value,)
        else:
            if false_value is None:
                raise RuntimeError("false_value was not evaluated (lazy gate failed)")
            logger.debug(f"[BASIFY Lazy Conditional Switch] Returning false_value of type {type(false_value).__name__}")
            return (false_value,)


NODE_CLASS_MAPPINGS = {
    "BasifyLazyConditionalSwitch": LazyConditionalSwitch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyLazyConditionalSwitch": "Basify: Lazy Conditional Switch",
}
