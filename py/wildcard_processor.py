import logging
import time
from pathlib import Path
try:
    from .wildcard_handler import process_wildcards_in_text
except ImportError:
    # Fallback for when imported outside of the package context
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    from wildcard_handler import process_wildcards_in_text

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
_wildcard_output_cache = {}
_MAX_CACHE_SIZE = 100

class WildcardProcessor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "enable_wildcards": ("BOOLEAN", {"default": True}),
                "wildcard_directory": ("STRING", {"default": "/llm/models/image/wildcards"}),
                "force_refresh": ("STRING", {"default": ""})
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("processed_text", "original_text")
    OUTPUT_NODE = True
    DESCRIPTION = "Processes text with wildcards, replacing them with their corresponding values from files in the specified directory."
    FUNCTION = "process_text"
    CATEGORY = "utils"

    def __init__(self):
        self.display_text = ""
        self.wildcards_enabled = True
        self.wildcard_directory = "/llm/models/image/wildcards"
        self.opened_path = None

    def process_text(self, text, enable_wildcards=True, wildcard_directory="/llm/models/image/wildcards", force_refresh="", prompt=None, unique_id=None):
        """
        Process the input text and replace wildcards if enabled.
        
        Args:
            text (str): Input text with potential wildcard tokens
            enable_wildcards (bool): Whether wildcard processing is enabled
            wildcard_directory (str): Directory where wildcard files are stored
            prompt: Prompt information (ComfyUI internal)
            unique_id: Unique identifier for the node (ComfyUI internal)
            
        Returns:
            tuple: Processed text with wildcards replaced
        """
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
            return ("", "")
            
        if not enable_wildcards:
            logger.info(f"{Colors.BLUE}[BASIFY Wildcards Node]{Colors.ENDC} {Colors.YELLOW}Wildcards disabled, returning original text{Colors.ENDC}")
            self.display_text = text
            return (text, text)
            
        try:
            # Process wildcards in the text with force_refresh for increased randomness
            processed_text = process_wildcards_in_text(text, wildcard_directory, force_refresh)
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
            
            return (processed_text, text)

        except Exception as e:
            logger.error(f"{Colors.BLUE}[BASIFY Wildcards Node]{Colors.ENDC} {Colors.RED}Error processing wildcards: {e}{Colors.ENDC}")
            self.display_text = text  # Return original text on error
            return (text, text)

def _cleanup_cache():
    """Clean up old cache entries to prevent unbounded growth."""
    global _wildcard_output_cache
    keys_to_keep = None
    keys_to_remove = None
    
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
            
            # Clean up intermediate collections
            del keys_to_remove
            del keys_to_keep
    finally:
        # Ensure cleanup even on error
        if keys_to_remove is not None:
            del keys_to_remove
        if keys_to_keep is not None:
            del keys_to_keep

def get_latest_wildcard_output():
    """
    Get the most recently processed wildcard text.
    Returns None if no wildcard processing has occurred.
    """
    return _wildcard_output_cache.get("latest", None)

def get_wildcard_output_by_node_id(node_id):
    """
    Get the wildcard output for a specific node ID.
    Returns None if no output found for that node ID.
    """
    return _wildcard_output_cache.get(node_id, None)

def get_all_wildcard_outputs():
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
