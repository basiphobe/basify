import logging
import random
from typing import Any

# Logging setup
logger = logging.getLogger(__name__)

class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    ENDC = "\033[0m"

loggerName = f"{Colors.BLUE}BASIFY NumberRandomizer{Colors.ENDC}"


class NumberRandomizer:
    """
    A ComfyUI node that generates random or fixed numbers with configurable range.
    Supports both integer and float output types.
    """

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "step": 1,
                    "display": "number"
                }),
                "min_value": ("FLOAT", {
                    "default": 0.0,
                    "min": -1000000.0,
                    "max": 1000000.0,
                    "step": 0.01,
                    "display": "number"
                }),
                "max_value": ("FLOAT", {
                    "default": 100.0,
                    "min": -1000000.0,
                    "max": 1000000.0,
                    "step": 0.01,
                    "display": "number"
                }),
            }
        }

    RETURN_TYPES = ("INT", "FLOAT")
    RETURN_NAMES = ("int_value", "float_value")
    FUNCTION = "generate_number"
    CATEGORY = "basify"
    OUTPUT_NODE = False

    @classmethod
    def IS_CHANGED(cls, seed: int, **kwargs: Any) -> float:
        """Force re-execution on each run for new random values."""
        import time
        return time.time()

    def generate_number(
        self,
        seed: int,
        min_value: float,
        max_value: float
    ) -> tuple[int, float]:
        """
        Generate a random number based on the specified parameters.

        Args:
            seed: Random seed for reproducibility
            min_value: Minimum value of range
            max_value: Maximum value of range

        Returns:
            Tuple of (int_value, float_value)
        """
        try:
            # Validate range
            if min_value > max_value:
                logger.warning(f"[{loggerName}] min_value ({min_value}) > max_value ({max_value}), swapping")
                min_value, max_value = max_value, min_value

            # Initialize random with seed
            rng = random.Random(seed)

            # Generate float and derive int
            random_float = round(rng.uniform(min_value, max_value), 2)
            random_int = int(random_float)

            logger.info(
                f"[{loggerName}] {Colors.GREEN}Generated: "
                f"int={random_int}, float={random_float:.4f} "
                f"(seed={seed}, range=[{min_value}, {max_value}]){Colors.ENDC}"
            )

            return (random_int, random_float)

        except Exception as e:
            logger.error(f"[{loggerName}] Error generating number: {e}")
            # Return safe defaults
            return (0, 0.0)


# Node registration
NODE_CLASS_MAPPINGS = {
    "BasifyNumberRandomizer": NumberRandomizer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyNumberRandomizer": "Basify: Number Randomizer"
}
