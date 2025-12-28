import os
import datetime
import queue
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

import server
from aiohttp import web

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)

_last_image = None
_last_save_path = None

# Create a response queue
response_queue = queue.Queue()

@server.PromptServer.instance.routes.post("/basify/server/llm/save_again")
async def save_again(request):
    try:
        if _last_image is None or _last_save_path is None:
            return web.json_response({"status": "error", "message": "No image to re-save."})
        # Re-save the last image
        Image.fromarray(_last_image).save(_last_save_path)
        return web.json_response({"status": "success"})
    except Exception as e:
        logger.error(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.RED}Error re-saving image: {str(e)}{Colors.ENDC}")
        return web.json_response({"status": "error", "message": str(e)})

@server.PromptServer.instance.routes.post("/basify/server/llm/prompt_request")
async def process_prompt_response(request):
    data = await request.json()
    # Clear queue before adding new data to prevent old responses from being used
    while not response_queue.empty():
        try:
            response_queue.get_nowait()
        except queue.Empty:
            break
    response_queue.put(data)
    return web.json_response({"status": "success"})

class SaveImageCustomPath:
    """ComfyUI node for saving images with customizable paths and filenames."""
    lock = threading.Lock()
    # Store random values per workflow session to ensure consistency
    _session_values = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "custom_folder": ("STRING", {
                    "default": "output/comfy/{date}",
                    "multiline": False,
                    "tooltip": "Path with variables: {date} {time} {datetime} {timestamp} {year} {month} {day} {hour} {minute} {second} {random_number} {random_string} {uuid}\nExamples: /llm/output/{date}/{time} or /llm/output/{date}/{random_number}"
                }),
                "filename_prefix": ("STRING", {
                    "default": "generated_image",
                    "tooltip": "Supports variables: {date} {time} {random_number} etc.\nUse Python format strings like 'image_{:06d}' for custom counter padding (requires timestamp disabled)"
                }),
                "file_extension": (["png", "jpg", "webp"], {"default": "png"}),
                "use_timestamp": (["enable", "disable"], {"default": "enable", "tooltip": "Enable: adds date/time to filename. Disable: uses auto-incrementing counter"}),
                "save_metadata": (["enable", "disable"], {"default": "enable"})
            },
            "optional": {
                "text_content": ("STRING", {"default": "", "multiline": True}),
                "save_text": (["enable", "disable"], {"default": "disable"}),
                "session_id": ("STRING", {
                    "default": "",
                    "tooltip": "Optional: Set a custom session ID to persist random values ({uuid}, {random_number}, {random_string}) across multiple saves. Leave empty to auto-generate per node."
                })
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    FUNCTION = "save_image"
    CATEGORY = "basify"
    OUTPUT_NODE = True
    RETURN_NAMES = ("image", "saved_path",)

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
    def replace_path_variables(path, now=None, session_id=None):
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
        - {random_number} - Random 6-digit number (persists per session)
        - {random_string} - Random 8-character alphanumeric string (persists per session)
        - {uuid} - UUID4 first 8 characters (persists per session)
        
        Args:
            path: Path string with variables to replace
            now: datetime object to use for date/time variables
            session_id: Session ID for persisting random values
        """
        if now is None:
            now = datetime.datetime.now()
        
        # Use session_id to retrieve or generate random values
        if session_id and session_id in SaveImageCustomPath._session_values:
            # Reuse existing session values
            session_data = SaveImageCustomPath._session_values[session_id]
            random_number = session_data['random_number']
            random_string = session_data['random_string']
            uuid_string = session_data['uuid']
        else:
            # Generate new random values
            random_number = random.randint(100000, 999999)
            random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            uuid_string = str(uuid.uuid4())[:8]
            
            # Store for this session if session_id provided
            if session_id:
                SaveImageCustomPath._session_values[session_id] = {
                    'random_number': random_number,
                    'random_string': random_string,
                    'uuid': uuid_string
                }
        
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

    def save_image(self, image, custom_folder, filename_prefix, file_extension, use_timestamp, save_metadata, text_content="", save_text="disable", session_id="", prompt=None, extra_pnginfo=None, unique_id=None):
        logger.info(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.GREEN}Saving image with custom path: {custom_folder}{Colors.ENDC}")
        global _last_image, _last_save_path
        
        # Validate input is a tensor
        if not isinstance(image, torch.Tensor):
            logger.error(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.RED}Expected torch.Tensor, got {type(image)}{Colors.ENDC}")
            return (image, "")
        
        # Validate input is a tensor
        if not isinstance(image, torch.Tensor):
            logger.error(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.RED}Expected torch.Tensor, got {type(image)}{Colors.ENDC}")
            return (image, "")
        
        # Use unique_id as session_id if no custom session_id provided
        # This ensures all images from the same node instance use the same random values
        effective_session_id = session_id if session_id else (unique_id if unique_id else None)
        
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
                        save_folder = self.replace_path_variables(custom_folder, now, effective_session_id)
                        os.makedirs(save_folder, exist_ok=True)
                        
                        # Also support variables in filename prefix
                        filename_with_vars = self.replace_path_variables(filename_prefix, now, effective_session_id)
                        
                        # Generate filename with batch index
                        batch_suffix = f"_batch{batch_idx + 1}" if num_images > 1 else ""
                        
                        # Generate filename
                        if use_timestamp == "enable":
                            today = now.strftime('%Y-%m-%d')
                            timestamp = now.strftime('%H-%M-%S')
                            file_name = f"{filename_with_vars}_{today}_{timestamp}{batch_suffix}.{file_extension}"
                        else:
                            # Support Python format strings like {:06d} or fallback to auto-detection
                            format_match = re.search(r'\{:(\d*)d\}', filename_with_vars)
                            
                            if format_match:
                                # User provided explicit format string like {:06d}
                                padding_width = int(format_match.group(1)) if format_match.group(1) else 0
                                format_str = format_match.group(0)
                                
                                counter = 0
                                while True:
                                    # Replace the format string with the counter value
                                    formatted_name = filename_with_vars.replace(format_str, str(counter).zfill(padding_width) if padding_width else str(counter))
                                    file_name = f"{formatted_name}{batch_suffix}.{file_extension}"
                                    file_path = os.path.join(save_folder, file_name)
                                    if not os.path.exists(file_path):
                                        break
                                    counter += 1
                            else:
                                # Auto-detect needed padding based on existing files
                                existing_files = [f for f in os.listdir(save_folder) if f.endswith(f'.{file_extension}')]
                                max_existing = 0
                                for f in existing_files:
                                    # Extract numbers from filename
                                    numbers = re.findall(r'\d+', f)
                                    if numbers:
                                        max_existing = max(max_existing, max(int(n) for n in numbers))
                                
                                # Determine padding: use at least 3 digits, but expand if needed
                                padding_width = max(3, len(str(max_existing + 1000)))
                                
                                counter = 1
                                while True:
                                    file_name = f"{filename_with_vars}_{counter:0{padding_width}d}{batch_suffix}.{file_extension}"
                                    file_path = os.path.join(save_folder, file_name)
                                    if not os.path.exists(file_path):
                                        break
                                    counter += 1

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
                
            # Store last successfully saved image and path
            if saved_paths:
                _last_image = save_array
                _last_save_path = saved_paths[-1]
            
            # Return the original image tensor and all saved paths
            return (image, ";".join(saved_paths))
            
        except Exception as e:
            logger.error(f"{Colors.BLUE}[BASIFY save image]{Colors.ENDC} {Colors.RED}Error in batch processing: {str(e)}{Colors.ENDC}")
            return (image, "")

NODE_CLASS_MAPPINGS = {
    "BasifySaveImage": SaveImageCustomPath
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifySaveImage": "Basify: Save Image"
}
