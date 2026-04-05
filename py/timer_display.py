from typing import Any

from comfy.comfy_types.node_typing import IO


class TimerDisplay:
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, Any]]:
        return {
            "required": {},
            "optional": {
                "trigger": (IO.ANY, {
                    "tooltip": "Attach this to the end of a workflow branch so the timer node participates in execution."
                }),
            }
        }

    RETURN_TYPES = (IO.ANY,)
    RETURN_NAMES = ("trigger",)
    FUNCTION = "display_timer"
    CATEGORY = "basify"
    OUTPUT_NODE = True

    def display_timer(self, trigger: Any = None) -> tuple[Any]:
        return (trigger,)


NODE_CLASS_MAPPINGS = {
    "BasifyTimerDisplay": TimerDisplay
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyTimerDisplay": "Basify: Timer Display"
}
