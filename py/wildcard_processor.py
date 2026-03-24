import logging
import random
import time
from typing import Any
from pathlib import Path
try:
    from .wildcard_handler import process_wildcards_in_text  # type: ignore[misc]
except ImportError:
    # Fallback for when imported outside of the package context
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    from wildcard_handler import process_wildcards_in_text  # type: ignore[misc]

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)

# Global cache to store the most recent wildcard processing results
# This allows other modules (like save_image) to access the processed text
# Cache is limited to prevent memory issues
_wildcard_output_cache: dict[str, str] = {}
_MAX_CACHE_SIZE = 100

# Counter to ensure IS_CHANGED always returns unique values
_is_changed_counter = 0

class WildcardProcessor:
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, Any]]:
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "prompt_file_path": ("STRING", {
                    "default": "",
                    "tooltip": "Optional path to a text file. If provided and valid, file contents take precedence over textarea."
                }),
                "clip": ("CLIP", {"tooltip": "Optional CLIP model for text encoding"}),
                "enable_wildcards": ("BOOLEAN", {"default": True}),
                "wildcard_directory": ("STRING", {"default": "/AI/wildcards"}),
                "force_refresh": ("BOOLEAN", {"default": False}),
                "iterator_completed": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "When True, stops randomization to prevent infinite loops when iteration is complete"
                })
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "CONDITIONING")
    RETURN_NAMES = ("processed_text", "original_text", "conditioning")
    OUTPUT_NODE = True
    DESCRIPTION = "Processes text with wildcards, replacing them with their corresponding values from files in the specified directory. Optionally encodes with CLIP."
    FUNCTION = "process_text"
    CATEGORY = "utils"

    @classmethod
    def IS_CHANGED(cls, text: str, prompt_file_path: str = "", enable_wildcards: bool = True, wildcard_directory: str = "/AI/wildcards", force_refresh: bool = False, iterator_completed: bool = False, **kwargs: Any) -> float | str:
        """Return unique value when wildcards enabled to force re-execution."""
        if enable_wildcards and not iterator_completed:
            return time.time()
        return hash((text, prompt_file_path))

    def __init__(self):
        self.display_text: str = ""
        self.wildcards_enabled: bool = True
        self.wildcard_directory: str = "/AI/wildcards"
        self.opened_path: str | None = None

    def process_text(self, text: str, prompt_file_path: str = "", enable_wildcards: bool = True, wildcard_directory: str = "/AI/wildcards", force_refresh: bool = False, iterator_completed: bool = False, clip: Any = None, prompt: Any = None, unique_id: str | None = None) -> tuple[str, str, Any]:
        """Process text with wildcards. If file path provided and valid, use file contents. Otherwise use textarea."""
        # If file path provided and valid, use its contents
        if prompt_file_path and prompt_file_path.strip():
            try:
                file_path = Path(prompt_file_path.strip())
                if file_path.exists() and file_path.is_file():
                    text = file_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.error(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.RED}Error reading file: {e}{Colors.ENDC}")
        
        original_text = text
        
        if not text:
            return ("", "", None)
            
        if not enable_wildcards:
            conditioning = self._encode_with_clip(text, clip) if clip is not None else None
            return (text, original_text, conditioning)
            
        # Process wildcards
        try:
            processed_text: str = process_wildcards_in_text(text, wildcard_directory, str(time.time()))  # type: ignore[misc]
            conditioning = self._encode_with_clip(processed_text, clip) if clip is not None else None
            return (processed_text, original_text, conditioning)  # type: ignore[return-value]
        except Exception as e:
            logger.error(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.RED}Error: {e}{Colors.ENDC}")
            conditioning = self._encode_with_clip(text, clip) if clip is not None else None
            return (text, original_text, conditioning)

    def _encode_with_clip(self, text: str, clip: Any) -> Any:
        """
        Encode text using CLIP model to produce conditioning.
        
        Args:
            text (str): Text to encode
            clip: CLIP model instance
            
        Returns:
            Conditioning output for use in diffusion models
        """
        try:
            tokens = clip.tokenize(text)
            cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            conditioning = [[cond, {"pooled_output": pooled}]]
            logger.info(f"{Colors.BLUE}[BASIFY Wildcards Node]{Colors.ENDC} {Colors.GREEN}Successfully encoded text with CLIP{Colors.ENDC}")
            return conditioning
        except Exception as e:
            logger.error(f"{Colors.BLUE}[BASIFY Wildcards Node]{Colors.ENDC} {Colors.RED}Error encoding with CLIP: {e}{Colors.ENDC}")
            return None

def _cleanup_cache() -> None:
    """Clean up old cache entries to prevent unbounded growth."""
    global _wildcard_output_cache
    keys_to_keep: set[str] | None = None
    keys_to_remove: list[str] | None = None
    
    try:
        if len(_wildcard_output_cache) > _MAX_CACHE_SIZE:
            # Keep only the "latest" entry and node-specific entries (non-timestamp keys)
            keys_to_keep = {"latest"}
            
            # Keep node ID entries (they don't start with "latest_")
            for key in list(_wildcard_output_cache.keys()):
                if not str(key).startswith("latest_"):
                    keys_to_keep.add(key)
            
            # Remove timestamp-based entries
            keys_to_remove = [k for k in _wildcard_output_cache.keys() if k not in keys_to_keep]
            
            # Explicitly delete cached values before removing keys
            for key in keys_to_remove:
                del _wildcard_output_cache[key]
            
            logger.debug(f"{Colors.BLUE}[BASIFY Wildcards Node]{Colors.ENDC} Cleaned up cache, removed {len(keys_to_remove)} entries")
            
            # Don't delete here - let finally block handle cleanup
    finally:
        # Ensure cleanup even on error - use try/except since del removes from namespace
        try:
            del keys_to_remove
        except (NameError, UnboundLocalError):
            pass
        try:
            del keys_to_keep
        except (NameError, UnboundLocalError):
            pass

def get_latest_wildcard_output() -> str | None:
    """
    Get the most recently processed wildcard text.
    Returns None if no wildcard processing has occurred.
    """
    return _wildcard_output_cache.get("latest", None)

def get_wildcard_output_by_node_id(node_id: str) -> str | None:
    """
    Get the wildcard output for a specific node ID.
    Returns None if no output found for that node ID.
    """
    return _wildcard_output_cache.get(node_id, None)

def get_all_wildcard_outputs() -> dict[str, str]:
    """
    Get all cached wildcard outputs.
    Returns a dictionary of {node_id: processed_text}
    """
    return _wildcard_output_cache.copy()
            
# Registration
NODE_CLASS_MAPPINGS = {
    "BasifyWildcardProcessor": WildcardProcessor
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyWildcardProcessor": "Basify: Wildcard Processor"
}
