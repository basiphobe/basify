# pyright: reportMissingImports=false
import os
import json
import logging
from typing import Any
import folder_paths  # type: ignore

logger = logging.getLogger(__name__)

# Lazy imports for ComfyUI modules that might not be available during package loading
def get_comfy_modules():
    import comfy.sd  # type: ignore
    return comfy.sd

# Global storage for last selected checkpoints per directory
LAST_SELECTIONS_FILE = os.path.join(os.path.dirname(__file__), ".checkpoint_selections.json")

def load_last_selections() -> dict[str, str]:
    """Load the last selected checkpoints from disk"""
    try:
        if os.path.exists(LAST_SELECTIONS_FILE):
            with open(LAST_SELECTIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError, OSError) as e:
        logger.warning(f"Could not load checkpoint selections: {e}")
    return {}

def save_last_selection(directory_path: str, checkpoint: str) -> None:
    """Save the last selected checkpoint for a directory"""
    try:
        selections = load_last_selections()
        # Use absolute path as key for consistency
        abs_dir = os.path.abspath(directory_path)
        selections[abs_dir] = checkpoint
        with open(LAST_SELECTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(selections, f, indent=2)
    except (IOError, OSError) as e:
        logger.warning(f"Could not save checkpoint selection: {e}")

def get_last_selection(directory_path: str) -> str:
    """Get the last selected checkpoint for a directory"""
    try:
        selections = load_last_selections()
        abs_dir = os.path.abspath(directory_path)
        return selections.get(abs_dir, "")
    except (OSError, ValueError) as e:
        logger.warning(f"Could not get last selection for {directory_path}: {e}")
        return ""


class DirectoryCheckpointScanner:
    """
    A directory scanner that finds all checkpoint models in a given directory
    (and subdirectories) and allows selection of one to load. Models are listed
    alphabetically with subdirectory paths included.
    """
    
    def __init__(self):
        self.checkpoint_extensions = ['.ckpt', '.safetensors', '.pt', '.pth']
    
    def scan_directory_for_checkpoints(self, directory_path: str) -> list[str]:
        """Scan directory and subdirectories for checkpoint files, following symbolic links."""
        checkpoints: list[str] = []
        seen_real_paths: set[str] = set()  # Track real paths to avoid duplicates
        
        if not directory_path:
            return ["No directory path provided"]
        
        if not os.path.exists(directory_path):
            return ["Directory does not exist"]
        
        if not os.path.isdir(directory_path):
            return ["Path is not a directory"]
        
        try:
            # Use os.walk with followlinks=True to support symbolic links
            for root, _dirs, files in os.walk(directory_path, followlinks=True):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in self.checkpoint_extensions):
                        full_path = os.path.join(root, file)
                        
                        # Resolve symbolic links to get the real path for deduplication
                        try:
                            real_path = os.path.realpath(full_path)
                            
                            # Skip if we've already seen this real path
                            if real_path in seen_real_paths:
                                continue
                            
                            seen_real_paths.add(real_path)
                            
                            # Create display name with subdirectory if applicable
                            rel_path = os.path.relpath(full_path, directory_path)
                            
                            # Add symbolic link indicator with relative path to target
                            if os.path.islink(full_path):
                                try:
                                    target_rel = os.path.relpath(real_path, directory_path)
                                    rel_path += f" → {target_rel}"
                                except ValueError:
                                    # If paths are on different drives (Windows), use basename
                                    rel_path += f" → {os.path.basename(real_path)}"
                            
                            checkpoints.append(rel_path)
                        except (OSError, ValueError) as e:
                            logger.warning(f"Could not process {full_path}: {e}")
                            continue
            
            # Sort alphabetically
            checkpoints.sort()
            
            if not checkpoints:
                return ["No checkpoints found"]
                
            return checkpoints
            
        except PermissionError as e:
            logger.error(f"Permission denied scanning {directory_path}: {e}")
            return [f"Permission denied: {str(e)}"]
        except OSError as e:
            logger.error(f"OS error scanning {directory_path}: {e}")
            return [f"Error scanning directory: {str(e)}"]
        except Exception as e:
            logger.error(f"Unexpected error scanning {directory_path}: {e}")
            return [f"Error scanning directory: {str(e)}"]
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, Any]]:
        # Default to ComfyUI's checkpoints directory
        try:
            checkpoint_paths = folder_paths.get_folder_paths("checkpoints")
            default_checkpoint_dir = checkpoint_paths[0] if checkpoint_paths else ""
        except (IndexError, AttributeError, KeyError):
            default_checkpoint_dir = ""
        
        # Get the last selected checkpoint for the default directory
        last_checkpoint = get_last_selection(default_checkpoint_dir) if default_checkpoint_dir else ""
        
        return {
            "required": {
                "directory_path": ("STRING", {
                    "default": default_checkpoint_dir,
                    "tooltip": "Directory to scan for checkpoint models (scans subdirectories, follows symbolic links, deduplicates)"
                }),
                "selected_checkpoint": ("STRING", {
                    "default": last_checkpoint,
                    "tooltip": "Select which checkpoint to load (last selection is remembered per directory)",
                    "serialize": True
                })
            }
        }
    
    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "full_path")
    FUNCTION = "process"
    CATEGORY = "loaders"
    DESCRIPTION = "Scans a directory for checkpoint models with symbolic link support, deduplication, and last selection memory"
    
    def process(self, directory_path: str, selected_checkpoint: str) -> tuple[Any, Any, Any, str]:
        """Main processing function that loads selected checkpoint."""
        
        # Validate directory path
        if not directory_path:
            logger.warning("No directory path provided")
            return (None, None, None, "")
        
        if not os.path.exists(directory_path):
            logger.warning(f"Directory does not exist: {directory_path}")
            return (None, None, None, "")
        
        # If no valid checkpoint is selected, return empty results
        invalid_selections = {
            "", "Click to refresh", "No checkpoints found", 
            "Directory does not exist", "Path is not a directory",
            "No directory path provided", "Permission denied"
        }
        
        if (not selected_checkpoint or 
            selected_checkpoint in invalid_selections or
            selected_checkpoint.startswith("Error scanning") or
            selected_checkpoint.startswith("Permission denied")):
            return (None, None, None, "")
        
        # Handle symbolic link display names (remove the "→ path" part)
        clean_checkpoint = selected_checkpoint.split(" → ")[0] if " → " in selected_checkpoint else selected_checkpoint
        
        # Build full path to selected checkpoint
        full_checkpoint_path = os.path.join(directory_path, clean_checkpoint)
        
        # Resolve symbolic links to get the actual file path
        try:
            if os.path.islink(full_checkpoint_path):
                resolved_path = os.path.realpath(full_checkpoint_path)
                if os.path.exists(resolved_path):
                    full_checkpoint_path = resolved_path
                else:
                    logger.error(f"Symbolic link target does not exist: {resolved_path}")
                    return (None, None, None, "")
            elif not os.path.exists(full_checkpoint_path):
                logger.error(f"Checkpoint file does not exist: {full_checkpoint_path}")
                return (None, None, None, "")
        except (OSError, ValueError) as e:
            logger.error(f"Error resolving checkpoint path {full_checkpoint_path}: {e}")
            return (None, None, None, "")
        
        # Save the last selection for this directory
        save_last_selection(directory_path, selected_checkpoint)
        
        try:
            # Get the modules when needed
            comfy_sd = get_comfy_modules()
            
            # Load the checkpoint
            logger.info(f"Loading checkpoint: {full_checkpoint_path}")
            model, clip, vae = comfy_sd.load_checkpoint_guess_config(  # type: ignore[misc]
                full_checkpoint_path, 
                output_vae=True, 
                output_clip=True, 
                embedding_directory=folder_paths.get_folder_paths("embeddings")
            )[:3]
            
            logger.info(f"Successfully loaded checkpoint: {os.path.basename(full_checkpoint_path)}")
            return (model, clip, vae, full_checkpoint_path)
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint {full_checkpoint_path}: {e}")
            # Explicitly clean up any partially loaded objects
            import gc
            gc.collect()
            return (None, None, None, "")


# Export the node
NODE_CLASS_MAPPINGS = {
    "DirectoryCheckpointScanner": DirectoryCheckpointScanner
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DirectoryCheckpointScanner": "Basify: Directory Checkpoint Scanner"
}
