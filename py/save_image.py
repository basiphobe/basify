import os
import datetime
import numpy as np
import threading
import random
import string
import uuid
import re
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import torch
import json
import logging

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)

class SaveImageCustomPath:
    """ComfyUI node for saving images with customizable paths and filenames."""
    lock = threading.Lock()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "custom_folder": ("STRING", {
                    "default": "output/comfy/{date}",
                    "multiline": False,
                    "tooltip": "Path with variables: {date} {time} {datetime} {timestamp} {year} {month} {day} {hour} {minute} {second} {random_number} {random_string} {uuid}\nFormat strings work here too: folder_{:04d}\nExamples: /llm/output/{date}/{time} or /llm/output/{date}/{random_number}"
                }),
                "filename_prefix": ("STRING", {
                    "default": "generated_image_{date}_{time}",
                    "tooltip": "Supports all path variables: {date} {time} {random_number} etc.\nUse Python format strings for auto-increment: frame_{:06d} or image_{:04d}\nCounter starts at 0 and increments automatically."
                }),
                "file_extension": (["png", "jpg", "webp"], {"default": "png"}),
                "save_metadata": (["enable", "disable"], {"default": "enable"}),
                "save_text": (["enable", "disable"], {"default": "disable"}),
            },
            "optional": {
                "text_content": ("STRING", {"default": "", "multiline": True}),
                "session_uuid": ("STRING", {
                    "default": "",
                    "tooltip": "Optional: UUID from a previous save node to share the same folder. Leave empty to generate a new UUID. Connect this to the 'uuid' output of another save node to daisy-chain."
                })
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING",)
    FUNCTION = "save_image"
    CATEGORY = "basify"
    OUTPUT_NODE = True
    RETURN_NAMES = ("image", "saved_path", "uuid",)

    @staticmethod
    def _save_image_file(image_to_save, file_path, file_extension, metadata_enabled, prompt=None, extra_pnginfo=None):
        """Helper method to save image with appropriate format and metadata."""
        if metadata_enabled and file_extension.lower() == 'png':
            # Match ComfyUI's native SaveImage format exactly for drag-and-drop support
            metadata = PngInfo()
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata.add_text(x, json.dumps(extra_pnginfo[x]))
            image_to_save.save(file_path, format='PNG', pnginfo=metadata)
        elif file_extension.lower() == 'png':
            image_to_save.save(file_path, format='PNG')
        elif file_extension.lower() == 'jpg':
            image_to_save.save(file_path, format='JPEG', quality=95)
        elif file_extension.lower() == 'webp':
            image_to_save.save(file_path, format='WEBP', quality=95)
        else:
            image_to_save.save(file_path)

    @staticmethod
    def replace_path_variables(path, now=None, uuid_value=None):
        """Replace all dynamic variables in the path string.
        
        Supported variables:
        - {date} - Current date in YYYY-MM-DD format
        - {time} - Current time in HH-MM-SS format
        - {datetime} - Current datetime in YYYY-MM-DD_HH-MM-SS format
        - {timestamp} - Unix timestamp
        - {year} - Current year (YYYY)
        - {month} - Current month (MM)
        - {day} - Current day (DD)
        - {hour} - Current hour (HH)
        - {minute} - Current minute (MM)
        - {second} - Current second (SS)
        - {random_number} - Random 6-digit number
        - {random_string} - Random 8-character alphanumeric string
        - {uuid} - UUID4 first 8 characters (or provided uuid_value)
        
        Note: Python format strings like {:06d} are preserved and handled separately during counter generation.
        
        Args:
            path: Path string with variables to replace
            now: datetime object to use for date/time variables
            uuid_value: Optional UUID value to use for {uuid} token
        """
        if now is None:
            now = datetime.datetime.now()
        
        # Generate random values (fresh each time unless uuid_value provided)
        random_number = random.randint(100000, 999999)
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        uuid_string = uuid_value if uuid_value else str(uuid.uuid4())[:8]
        
        # Replace all variables
        replacements = {
            '{date}': now.strftime('%Y-%m-%d'),
            '{time}': now.strftime('%H-%M-%S'),
            '{datetime}': now.strftime('%Y-%m-%d_%H-%M-%S'),
            '{timestamp}': str(int(now.timestamp())),
            '{year}': now.strftime('%Y'),
            '{month}': now.strftime('%m'),
            '{day}': now.strftime('%d'),
            '{hour}': now.strftime('%H'),
            '{minute}': now.strftime('%M'),
            '{second}': now.strftime('%S'),
            '{random_number}': str(random_number),
            '{random_string}': random_string,
            '{uuid}': uuid_string,
        }
        
        for variable, value in replacements.items():
            path = path.replace(variable, value)
        
        return path

    def save_image(self, image, custom_folder, filename_prefix, file_extension, save_metadata, text_content="", save_text="disable", session_uuid="", prompt=None, extra_pnginfo=None, unique_id=None):
        logger.info(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.GREEN}Saving image with custom path: {custom_folder}{Colors.ENDC}")
        
        # Handle empty string from old workflows for save_text
        if save_text == "":
            save_text = "disable"
        
        # Validate input is a tensor
        if not isinstance(image, torch.Tensor):
            logger.error(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.RED}Expected torch.Tensor, got {type(image)}{Colors.ENDC}")
            return (image, "", "")
        
        # Use provided session_uuid or generate a new one
        if session_uuid and session_uuid.strip():
            folder_uuid = session_uuid.strip()
        else:
            folder_uuid = str(uuid.uuid4())[:8]
        
        saved_paths = []
        save_array = None  # Initialize to avoid potential unbound variable
        
        try:
            # Convert tensor to numpy array for saving
            save_tensor = image.cpu() if image.is_cuda else image
            original_shape = save_tensor.shape
            
            # Get number of images in batch
            num_images = original_shape[0] if len(original_shape) == 4 else 1
            logger.info(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.GREEN}Number of images in batch: {num_images}{Colors.ENDC}")
            
            # Process each image in the batch
            for batch_idx in range(num_images):
                logger.debug(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.GREEN}Processing batch image {batch_idx + 1}/{num_images}{Colors.ENDC}")
                
                try:
                    # Handle different tensor shapes for current batch image
                    if len(original_shape) == 4:  # [B, H, W, C] or [B, C, H, W]
                        if original_shape[-1] == 3:  # [B, H, W, 3]
                            current_tensor = save_tensor[batch_idx]
                        elif original_shape[1] == 3:  # [B, 3, H, W]
                            current_tensor = save_tensor[batch_idx].permute(1, 2, 0)
                        else:
                            logger.error(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.RED}Unexpected 4D tensor shape: {original_shape}{Colors.ENDC}")
                            continue
                    elif len(original_shape) == 3:  # [C, H, W] or [H, W, C]
                        if original_shape[0] == 3:  # [3, H, W]
                            current_tensor = save_tensor.permute(1, 2, 0)
                        else:
                            current_tensor = save_tensor
                    else:
                        logger.error(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.RED}Unexpected tensor shape: {original_shape}{Colors.ENDC}")
                        continue

                    save_array = current_tensor.squeeze().numpy()

                    # Validate final shape
                    if not (len(save_array.shape) == 3 and save_array.shape[-1] == 3):
                        if len(save_array.shape) == 2:
                            # Grayscale - convert to RGB
                            save_array = np.stack([save_array] * 3, axis=-1)
                        else:
                            logger.error(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.RED}Invalid final shape: {save_array.shape}{Colors.ENDC}")
                            continue

                    # Normalize values to [0, 1] range first
                    if save_array.min() < 0 or save_array.max() > 1:
                        save_array = (save_array - save_array.min()) / (save_array.max() - save_array.min())

                    # Handle any remaining negative zeros
                    save_array = np.abs(save_array)
                
                    # Normalize value range to uint8
                    save_array = (save_array * 255 if save_array.max() <= 1.0 else save_array).astype('uint8')
                    image_to_save = Image.fromarray(save_array)

                    with self.lock:
                        # Generate path with variable substitution
                        now = datetime.datetime.now()
                        
                        # Process both folder and filename - check for format strings BEFORE variable replacement
                        folder_format_match = re.search(r'\{:(\d*)d\}', custom_folder)
                        filename_format_match = re.search(r'\{:(\d*)d\}', filename_prefix)
                        
                        # Determine if we're using counter mode (format string anywhere in path or filename)
                        using_counter = folder_format_match or filename_format_match
                        
                        if using_counter:
                            # Extract format details
                            if folder_format_match:
                                format_str = folder_format_match.group(0)
                                padding_width = int(folder_format_match.group(1)) if folder_format_match.group(1) else 0
                                template_folder = custom_folder
                            else:
                                format_str = filename_format_match.group(0)
                                padding_width = int(filename_format_match.group(1)) if filename_format_match.group(1) else 0
                                template_folder = custom_folder
                            
                            template_filename = filename_prefix
                            
                            # Find next available counter
                            counter = 0
                            while True:
                                # Replace format string with counter value
                                counter_str = str(counter).zfill(padding_width) if padding_width else str(counter)
                                
                                # Apply counter to folder and filename templates
                                current_folder = template_folder.replace(format_str, counter_str) if folder_format_match else template_folder
                                current_filename = template_filename.replace(format_str, counter_str) if filename_format_match else template_filename
                                
                                # Now do variable substitution
                                # Use folder_uuid for folder (to group nodes), None for filename (to keep unique per node)
                                save_folder = self.replace_path_variables(current_folder, now, folder_uuid)
                                filename_with_vars = self.replace_path_variables(current_filename, now, None)
                                
                                # In counter mode, don't add batch suffix - counter handles uniqueness
                                file_name = f"{filename_with_vars}.{file_extension}"
                                file_path = os.path.join(save_folder, file_name)
                                
                                # Create folder if needed and check if file exists
                                os.makedirs(save_folder, exist_ok=True)
                                if not os.path.exists(file_path):
                                    break
                                counter += 1
                        else:
                            # No counter mode - just do variable substitution
                            # Use folder_uuid for folder (to group nodes), None for filename (to keep unique per node)
                            save_folder = self.replace_path_variables(custom_folder, now, folder_uuid)
                            os.makedirs(save_folder, exist_ok=True)
                            
                            filename_with_vars = self.replace_path_variables(filename_prefix, now, None)
                            batch_suffix = f"_batch{batch_idx + 1}" if num_images > 1 else ""
                            file_name = f"{filename_with_vars}{batch_suffix}.{file_extension}"
                            file_path = os.path.join(save_folder, file_name)

                        # Save image using helper method
                        metadata_enabled = (save_metadata == "enable")
                        logger.debug(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.GREEN}Saving {'with' if metadata_enabled else 'without'} metadata{Colors.ENDC}")
                        self._save_image_file(image_to_save, file_path, file_extension, metadata_enabled, prompt, extra_pnginfo)

                        # Save text file if enabled and text content is provided
                        if save_text == "enable" and text_content.strip():
                            try:
                                # Generate text file path with same name as image but .txt extension
                                text_file_path = os.path.splitext(file_path)[0] + ".txt"
                                
                                with open(text_file_path, 'w', encoding='utf-8') as text_file:
                                    text_file.write(text_content)
                                
                                logger.info(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.GREEN}Text file saved: {text_file_path}{Colors.ENDC}")
                            except Exception as e:
                                logger.error(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.RED}Error saving text file: {str(e)}{Colors.ENDC}")

                        saved_paths.append(file_path)

                except Exception as e:
                    logger.error(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.RED}Error saving batch image {batch_idx}: {str(e)}{Colors.ENDC}")
                    continue  # Continue to next image instead of returning
            
            # Explicitly delete large arrays to free memory
            del save_tensor
            if save_array is not None:
                del save_array
            
            # Return the original image tensor, all saved paths, and the UUID used
            return (image, ";".join(saved_paths), folder_uuid)
            
        except Exception as e:
            logger.error(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.RED}Error in batch processing: {str(e)}{Colors.ENDC}")
            return (image, "", "")

NODE_CLASS_MAPPINGS = {
    "BasifySaveImage": SaveImageCustomPath
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifySaveImage": "Basify: Save Image"
}
