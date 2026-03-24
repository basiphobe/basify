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
                "prompt_file_path": ("STRING", {"default": ""}),
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
        """
        Tell ComfyUI when to re-execute this node.
        When wildcards are enabled and iteration is active, return a new value to generate random results.
        When iteration is complete, return a consistent value to stop re-execution.
        """
        # Only stop randomizing if explicitly told to via iterator_completed input
        if iterator_completed:
            logger.info(f"{Colors.BLUE}[BASIFY Wildcards IS_CHANGED]{Colors.ENDC} {Colors.GREEN}STOPPING - iteration complete, returning hash{Colors.ENDC}")
            return hash(text)
        
        if enable_wildcards:
            # Return current timestamp + counter to force re-execution every time wildcards are enabled
            # Combined with counter to ensure uniqueness even with rapid successive calls
            global _is_changed_counter
            _is_changed_counter += 1
            unique_value = time.time() + (_is_changed_counter * 0.000001)
            return unique_value
        # Return a constant when wildcards are disabled to allow caching
        return ""

    def __init__(self):
        self.display_text: str = ""
        self.wildcards_enabled: bool = True
        self.wildcard_directory: str = "/AI/wildcards"
        self.opened_path: str | None = None

    def process_text(self, text: str, prompt_file_path: str = "", enable_wildcards: bool = True, wildcard_directory: str = "/AI/wildcards", force_refresh: bool = False, iterator_completed: bool = False, clip: Any = None, prompt: Any = None, unique_id: str | None = None) -> tuple[str, str, Any]:
        """
        Process the input text and replace wildcards if enabled.
        
        Args:
            text (str): Input text with potential wildcard tokens
            enable_wildcards (bool): Whether wildcard processing is enabled
            wildcard_directory (str): Directory where wildcard files are stored
            force_refresh (bool): Force refresh to increase randomness
            iterator_completed (bool): Whether iteration is complete (stops randomization)
            clip: Optional CLIP model for text encoding
            prompt: Prompt information (ComfyUI internal)
            unique_id: Unique identifier for the node (ComfyUI internal)
            
        Returns:
            tuple: Processed text with wildcards replaced, original text, and conditioning (if CLIP provided)
        """
        # If file path provided and valid, use it
        if prompt_file_path and prompt_file_path.strip():
            try:
                file_path = Path(prompt_file_path.strip())
                if file_path.exists() and file_path.is_file():
                    text = file_path.read_text(encoding='utf-8')
            except Exception:
                pass
        
        self.wildcards_enabled = enable_wildcards
        self.wildcard_directory = wildcard_directory
        
        # Update the opened_path if the wildcard directory changed or hasn't been set yet
        if wildcard_directory:
            try:
                if wildcard_directory.startswith('.'):
                    # Handle relative path
                    comfyui_root = Path(__file__).parent.parent.parent.parent  # Go up to ComfyUI root
                    abs_path = (comfyui_root / wildcard_directory).resolve()
                else:
                    abs_path = Path(wildcard_directory).resolve()
                self.opened_path = str(abs_path)
            except Exception as e:
                logger.warning(f"{Colors.BLUE}[BASIFY Wildcards Node]{Colors.ENDC} {Colors.YELLOW}Error resolving directory path: {e}{Colors.ENDC}")
        
        if not text:
            logger.info(f"{Colors.BLUE}[BASIFY Wildcards Node]{Colors.ENDC} {Colors.YELLOW}No input text provided{Colors.ENDC}")
            self.display_text = ""
            return ("", "", None)
            
        if not enable_wildcards:
            logger.info(f"{Colors.BLUE}[BASIFY Wildcards Node]{Colors.ENDC} {Colors.YELLOW}Wildcards disabled, returning original text{Colors.ENDC}")
            self.display_text = text
            # Encode with CLIP if provided
            conditioning = self._encode_with_clip(text, clip) if clip is not None else None
            return (text, text, conditioning)
            
        try:
            # Process wildcards in the text - always use timestamp for randomness between runs
            # force_refresh adds extra entropy on top of base randomization
            refresh_seed = str(time.time())
            if force_refresh:
                # Add extra entropy when force_refresh is enabled
                refresh_seed = f"{refresh_seed}_{random.random()}"
            processed_text: str = process_wildcards_in_text(text, wildcard_directory, refresh_seed)  # type: ignore[misc]
            logger.info(f"{Colors.BLUE}[BASIFY Wildcards Node]{Colors.ENDC} {Colors.GREEN}Successfully processed wildcards in text{Colors.ENDC}")
            self.display_text = processed_text  # Store for display
            
            # Store in global cache with unique_id as key for other modules to access
            if unique_id:
                _wildcard_output_cache[unique_id] = processed_text
                logger.debug(f"{Colors.BLUE}[BASIFY Wildcards Node]{Colors.ENDC} {Colors.GREEN}Cached processed text for node {unique_id}: {processed_text[:100]}...{Colors.ENDC}")
            
            # Always store as "latest" for easy access
            _wildcard_output_cache["latest"] = processed_text
            
            # Clean up old cache entries if cache is too large
            _cleanup_cache()
            
            # Encode with CLIP if provided
            conditioning = self._encode_with_clip(processed_text, clip) if clip is not None else None
            
            return (processed_text, text, conditioning)  # type: ignore[return-value]

        except Exception as e:
            logger.error(f"{Colors.BLUE}[BASIFY Wildcards Node]{Colors.ENDC} {Colors.RED}Error processing wildcards: {e}{Colors.ENDC}")
            self.display_text = text  # Return original text on error
            conditioning = self._encode_with_clip(text, clip) if clip is not None else None
            return (text, text, conditioning)

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
