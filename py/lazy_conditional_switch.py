import logging
from typing import Any

try:
    from comfy.comfy_types.node_typing import IO  # type: ignore[import]
except Exception:  # pragma: no cover - comfy types unavailable in static analysis/runtime
    class IO:  # minimal fallback for static analysis and tests
        ANY = "ANY"

try:
    from comfy_execution.graph import ExecutionBlocker  # type: ignore[import]
except Exception:  # pragma: no cover - comfy execution unavailable in static analysis/runtime
    class ExecutionBlocker:  # minimal fallback for static analysis and tests
        def __init__(self, value):
            self.value = value

logger = logging.getLogger(__name__)


class LazyConditionalSwitch:
    """ComfyUI node that implements lazy conditional branching with optional execution blocking.
    
    This node evaluates only the selected branch based on a boolean condition,
    avoiding expensive computations on the unselected branch. Branch inputs are
    optional - if the selected branch is not connected, the node returns an
    ExecutionBlocker to halt downstream execution.
    
    This is critical for workflows where:
    - One branch triggers heavy GPU operations that should be bypassed when not needed
    - Execution should halt when a condition is met (e.g., iterator completion)
    
    Only the input corresponding to the condition value is evaluated - the other
    remains completely unevaluated, preventing any upstream nodes from executing.
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, Any]]:
        return {
            "required": {
                "condition": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Boolean condition. If True, evaluates true_value. If False, evaluates false_value."
                }),
            },
            "optional": {
                "true_value": (IO.ANY, {
                    "lazy": True,
                    "tooltip": "Value to evaluate and return when condition is True. If not connected, returns ExecutionBlocker to halt execution."
                }),
                "false_value": (IO.ANY, {
                    "lazy": True,
                    "tooltip": "Value to evaluate and return when condition is False. If not connected, returns ExecutionBlocker to halt execution."
                }),
            }
        }
    
    RETURN_TYPES = (IO.ANY,)  # type: ignore[misc]
    RETURN_NAMES = ("value",)
    FUNCTION = "switch"
    CATEGORY = "basify"
    
    def check_lazy_status(self, condition: bool, **kwargs) -> list[str]:
        """Determine which inputs need to be evaluated based on the condition.
        
        This method is called by ComfyUI's lazy evaluation system before executing
        the main function. It returns a list of input names that need to be evaluated.
        
        Connected but unevaluated lazy inputs are passed as None in kwargs.
        Unconnected optional inputs are not present in kwargs.
        
        Args:
            condition: The boolean condition value (always evaluated first)
            **kwargs: May contain 'true_value' and/or 'false_value' if connected
            
        Returns:
            list[str]: Names of inputs that need to be evaluated (empty if selected input
                      is not connected or already evaluated)
        """
        # Defensive: convert to bool in case condition is int/float (0/1) from comparison nodes
        cond = bool(condition)
        
        # Determine which branch is selected
        selected_key = "true_value" if cond else "false_value"
        
        # Only request evaluation if:
        # 1. The selected input is connected (present in kwargs), AND
        # 2. It hasn't been evaluated yet (value is None)
        if selected_key in kwargs and kwargs[selected_key] is None:
            logger.debug(f"[BASIFY Lazy Conditional Switch] Condition is {cond}, evaluating {selected_key}")
            return [selected_key]
        
        # Selected input is either:
        # - Not connected (will return ExecutionBlocker in switch())
        # - Already evaluated (ready to return in switch())
        return []
    
    def switch(self, condition: bool, **kwargs) -> tuple[Any]:
        """Execute the conditional switch and return the selected value or ExecutionBlocker.
        
        This function is called after check_lazy_status has determined which inputs
        to evaluate. If the selected branch is connected, it returns the evaluated value.
        If the selected branch is not connected, it returns ExecutionBlocker(None) to
        halt downstream execution.
        
        Args:
            condition: The boolean condition value
            **kwargs: May contain 'true_value' and/or 'false_value' if connected and evaluated
            
        Returns:
            tuple: (selected_value,) or (ExecutionBlocker(None),) if selected branch not connected
        """
        # Defensive: convert to bool in case condition is int/float (0/1) from comparison nodes
        cond = bool(condition)
        
        # Determine which branch is selected
        selected_key = "true_value" if cond else "false_value"
        
        # Check if selected branch is connected
        if selected_key not in kwargs:
            # Selected branch is not connected - return ExecutionBlocker to halt execution
            logger.debug(f"[BASIFY Lazy Conditional Switch] {selected_key} not connected, returning ExecutionBlocker")
            return (ExecutionBlocker(None),)
        
        # Selected branch is connected - return its value
        selected_value = kwargs[selected_key]
        
        # Sanity check: if we got here, the value should have been evaluated by check_lazy_status
        if selected_value is None:
            raise RuntimeError(f"{selected_key} was not evaluated (lazy gate failed)")
        
        logger.debug(f"[BASIFY Lazy Conditional Switch] Returning {selected_key} of type {type(selected_value).__name__}")
        return (selected_value,)


NODE_CLASS_MAPPINGS = {
    "BasifyLazyConditionalSwitch": LazyConditionalSwitch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyLazyConditionalSwitch": "Basify: Lazy Conditional Switch",
}
