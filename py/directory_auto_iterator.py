import os
import glob
import json
from PIL import Image, ImageOps
import torch
import numpy as np

class DirectoryAutoIterator:
    """
    A ComfyUI node that automatically iterates through all images in a directory.
    Each workflow execution processes the next image in sequence.
    Tracks progress and stops when all images are processed.
    """
    
    def __init__(self):
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif']
        self.state_dir = os.path.join(os.path.dirname(__file__), '.directory_states')
        os.makedirs(self.state_dir, exist_ok=True)
        
    def get_state_file_path(self, directory_path):
        """Get the path for the state file for this directory."""
        if not directory_path:
            return None
        # Create a safe filename from the directory path
        safe_name = directory_path.replace('/', '_').replace('\\', '_').replace(':', '_')
        return os.path.join(self.state_dir, f"directory_state_{safe_name}.json")
    
    def load_state(self, directory_path):
        """Load the current state for this directory."""
        state_file = self.get_state_file_path(directory_path)
        if not state_file or not os.path.exists(state_file):
            return {"processed_files": [], "directory_path": directory_path, "completed": False}
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
                # Migrate old index-based state to new filename-based state
                if "current_index" in state and "processed_files" not in state:
                    state["processed_files"] = []
                    state.pop("current_index", None)
                return state
        except Exception as e:
            print(f"Error loading state: {e}")
            return {"processed_files": [], "directory_path": directory_path, "completed": False}
    
    def save_state(self, directory_path, state):
        """Save the current state for this directory."""
        state_file = self.get_state_file_path(directory_path)
        if not state_file:
            return
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def reset_state(self, directory_path):
        """Reset the state for this directory."""
        state = {"processed_files": [], "directory_path": directory_path, "completed": False}
        self.save_state(directory_path, state)
        return state
    
    def scan_directory_for_images(self, directory_path):
        """Scan directory for image files."""
        images = []
        
        if not os.path.exists(directory_path):
            return []
        
        try:
            images = []
            for file in os.listdir(directory_path):
                if any(file.lower().endswith(ext) for ext in self.image_extensions):
                    images.append(os.path.join(directory_path, file))
            
            # Sort alphabetically
            images.sort()
            return images
            
        except Exception as e:
            print(f"Error scanning directory: {str(e)}")
            return []
    
    def scan_directory_recursive(self, directory_path):
        """Scan directory and subdirectories for image files."""
        images = []
        
        if not os.path.exists(directory_path):
            return []
        
        try:
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in self.image_extensions):
                        full_path = os.path.join(root, file)
                        images.append(full_path)
            
            # Sort alphabetically
            images.sort()
            return images
            
        except Exception as e:
            print(f"Error scanning directory recursively: {str(e)}")
            return []
    
    def load_image_as_tensor(self, image_path):
        """Load an image file and convert it to ComfyUI tensor format."""
        img = None
        image_pil = None
        try:
            # Load image using PIL
            img = Image.open(image_path)
            
            # Handle EXIF orientation
            img = ImageOps.exif_transpose(img)
            
            # Convert to RGB if necessary
            image_pil = img.convert("RGB")
            
            # Convert to numpy array and normalize
            image_np = np.array(image_pil).astype(np.float32) / 255.0
            
            # Convert to tensor with shape [1, H, W, 3] (batch, height, width, channels)
            image_tensor = torch.from_numpy(image_np)[None,]
            
            # Create mask (for compatibility with Load Image node)
            if 'A' in img.getbands():
                mask_np = np.array(img.getchannel('A')).astype(np.float32) / 255.0
                mask_tensor = 1. - torch.from_numpy(mask_np)
                del mask_np
            else:
                mask_tensor = torch.zeros((image_np.shape[0], image_np.shape[1]), dtype=torch.float32)
            
            # Clean up intermediate objects
            del image_np
            if image_pil is not None:
                image_pil.close()
            if img is not None:
                img.close()
            
            return image_tensor, mask_tensor
            
        except Exception as e:
            print(f"Error loading image {image_path}: {str(e)}")
            # Clean up on error
            if image_pil is not None:
                image_pil.close()
            if img is not None:
                img.close()
            return None, None
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {
                    "default": "",
                    "tooltip": "Directory containing images to process automatically"
                }),
                "process_subdirectories": (["enable", "disable"], {
                    "default": "disable",
                    "tooltip": "Whether to include subdirectories in the scan"
                }),
                "reset_on_directory_change": (["enable", "disable"], {
                    "default": "enable",
                    "tooltip": "Reset to first image when directory path changes"
                })
            },
            "optional": {
                "reset_progress": (["false", "true"], {
                    "default": "false",
                    "tooltip": "Set to 'true' to reset and start from first image"
                })
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING", "INT", "INT", "BOOLEAN", "STRING")
    RETURN_NAMES = ("image", "mask", "file_path", "filename", "current_index", "total_count", "completed", "status")
    FUNCTION = "load_next_image"
    CATEGORY = "basify"
    DESCRIPTION = "Automatically iterates through all images in directory, one per workflow execution"
    
    @classmethod
    def IS_CHANGED(cls, directory_path, process_subdirectories, reset_on_directory_change, reset_progress="false"):
        """Force re-execution on every run to process the next image."""
        # This is the key - returning a random value forces ComfyUI to re-execute
        import random
        return random.random()
    
    def load_next_image(self, directory_path, process_subdirectories, reset_on_directory_change, reset_progress="false"):
        """Load the next image in the sequence."""
        
        # Validate directory path
        if not directory_path or not os.path.exists(directory_path):
            return (None, None, "", "", 0, 0, False, "Invalid directory path")
        
        # Check if reset is requested
        should_reset = reset_progress == "true"
        
        if should_reset:
            print(f"[DirectoryAutoIterator] Reset requested")
        
        # Always re-scan directory to pick up new/removed images
        if process_subdirectories == "enable":
            all_images = self.scan_directory_recursive(directory_path)
        else:
            all_images = self.scan_directory_for_images(directory_path)
        
        total_count = len(all_images)
        
        if total_count == 0:
            return (None, None, "", "", 0, 0, False, "No images found in directory")
        
        # Load current state
        state = self.load_state(directory_path)
        
        # Handle directory change
        if state.get("directory_path") != directory_path and reset_on_directory_change == "enable":
            state = self.reset_state(directory_path)
        
        # Handle manual reset - only if it hasn't been applied yet
        if should_reset:
            state = self.reset_state(directory_path)
        
        processed_files = set(state.get("processed_files", []))
        
        # Filter out already processed images
        unprocessed_images = [img for img in all_images if img not in processed_files]
        
        # Check if we've completed all images
        if not unprocessed_images:
            status = f"All images processed. Processed {len(processed_files)} total images."
            print(f"[DirectoryAutoIterator] {status}")
            state["completed"] = True
            self.save_state(directory_path, state)
            return (None, None, "", "", len(processed_files), total_count, False, status)
        
        # Try to load images until we find one that works
        image = None
        mask = None
        current_image_path = None
        filename = None
        
        for attempt_path in unprocessed_images:
            # Check if file still exists (handle race conditions)
            if not os.path.exists(attempt_path):
                print(f"[DirectoryAutoIterator] Skipping missing file: {attempt_path}")
                # Mark as processed to avoid trying again
                processed_files.add(attempt_path)
                continue
            
            # Try to load the image
            loaded_image, loaded_mask = self.load_image_as_tensor(attempt_path)
            if loaded_image is not None:
                # Successfully loaded
                current_image_path = attempt_path
                filename = os.path.basename(attempt_path)
                # Mark as processed
                processed_files.add(current_image_path)
                # Assign to final variables only when successful
                image = loaded_image
                mask = loaded_mask
                break
            else:
                # Failed to load, mark as processed and try next
                print(f"[DirectoryAutoIterator] Failed to load: {attempt_path}")
                processed_files.add(attempt_path)
        
        # Update state
        state["processed_files"] = list(processed_files)
        state["completed"] = len(processed_files) >= total_count
        self.save_state(directory_path, state)
        
        # If we couldn't load any image
        if image is None:
            status = f"All remaining images failed to load. Processed {len(processed_files)}/{total_count} images."
            print(f"[DirectoryAutoIterator] {status}")
            return (None, None, "", "", len(processed_files), total_count, False, status)
        
        # Successfully loaded an image
        remaining = len(all_images) - len(processed_files)
        status = f"Processing: {filename} ({len(processed_files)}/{total_count} processed, {remaining} remaining)"
        print(f"[DirectoryAutoIterator] {status}")
        
        # completed=True indicates a valid image is available for processing
        completed = True
        
        return (image, mask, current_image_path, filename, len(processed_files), total_count, completed, status)


# Export the node
NODE_CLASS_MAPPINGS = {
    "BasifyDirectoryAutoIterator": DirectoryAutoIterator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyDirectoryAutoIterator": "Basify: Directory Auto Iterator"
}