import logging
import os
import base64
import json
import requests
from io import BytesIO
from PIL import Image
import torch
import numpy as np

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)
loggerName = f"{Colors.BLUE}[BASIFY describe image]{Colors.ENDC}"

class DescribeImage:

    CATEGORY = "basify"
    FUNCTION = "describe_image"
    OUTPUT_NODE = True
    RETURN_NAMES = ("image", "description")
    RETURN_TYPES = ("IMAGE", "STRING",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "model": ("STRING", {"default": "llava:latest", "tooltip": "Ollama model to use for image description (must support vision)"}),
                "server_url": ("STRING", {"default": "http://localhost:11434/api/generate", "tooltip": "URL of the Ollama server API endpoint"}),
            },
            "optional": {
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.1, "tooltip": "Controls randomness of outputs"}),
                "max_tokens": ("INT", {"default": 500, "min": 10, "max": 4096, "tooltip": "Maximum number of tokens to generate"})
            }
        }

    def describe_image(self, image, model, server_url, temperature=0.7, max_tokens=500):
        buffered = None
        pil_image = None
        img_array = None
        
        try:
            logger.info(f"{loggerName} Processing image with model: {model}")
            
            # Convert the first image to a base64 string
            if len(image.shape) == 4:  # Batch of images
                img_tensor = image[0]  # Take the first image from the batch
            else:
                img_tensor = image  # Single image
                
            # Convert from tensor [H, W, C] to numpy array
            img_array = img_tensor.cpu().numpy()
            
            # Convert to uint8 if necessary
            if img_array.max() <= 1.0:
                img_array = (img_array * 255).astype(np.uint8)
            else:
                img_array = img_array.astype(np.uint8)
                
            # Convert to PIL image
            pil_image = Image.fromarray(img_array)
            
            # Save to BytesIO buffer
            buffered = BytesIO()
            pil_image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Close image objects immediately after encoding
            buffered.close()
            pil_image.close()
            # Don't delete or set to None - let finally block handle cleanup
            
            prompt = """
                DO describe the content of the image in detail. 
                DO return only a single description of the image. 
                DO return the description in a single sentence.

                AVOID any additional text or explanations. 
                AVOID returning anything other than a single description.
                AVOID repeating the prompt or instructions in the response.
                AVOID generating multiple descriptions or lists.
            """

            # Prepare the request payload for Ollama
            payload = {
                "model": model,
                "prompt": prompt,
                "images": [img_str],
                "stream": False,
                "temperature": temperature,
                "options": {
                    "num_predict": max_tokens
                }
            }
            
            # Don't delete here - let finally block handle cleanup
            
            logger.info(f"{loggerName} Sending request to Ollama server...")
            
            # Call the Ollama API
            response = requests.post(server_url, json=payload)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Parse the response
            result = response.json()
            response.close()  # Close the response connection
            
            if not result:
                logger.warning(f"{loggerName} Empty response from Ollama server")
                description = 'No description generated'
            else:
                description = result.get('response', 'No description generated').strip()
                if not description:
                    description = 'No description generated'
            
            logger.info(f"{loggerName} {Colors.BLUE} Successfully obtained image description: {Colors.ENDC}")
            logger.info(f"{loggerName} {Colors.GREEN}{description}{Colors.ENDC}")

            # Attempt to unload the model from memory
            try:
                logger.info(f"{loggerName} Unloading model: {model} from memory")
                unload_payload = {
                    "model": model,
                    "prompt": "",
                    "keep_alive": 0
                }
                unload_response = requests.post(server_url, json=unload_payload, timeout=5)
                unload_response.raise_for_status()
                unload_response.close()
                logger.info(f"{loggerName} Successfully unloaded model: {model}")
            except Exception as unload_error:
                logger.warning(f"{loggerName} {Colors.YELLOW}Failed to unload model {model}: {str(unload_error)}{Colors.ENDC}")
            
            return (image, description, )
        
        except Exception as e:
            logger.error(f"{Colors.RED}[BASIFY] Error in image description: {str(e)}{Colors.ENDC}")
            return (image, f"Error generating description: {str(e)}")
        
        finally:
            # Clean up any remaining objects - use try/except since del removes from namespace
            try:
                if buffered is not None:
                    buffered.close()
            except (NameError, UnboundLocalError):
                pass
            try:
                if pil_image is not None:
                    pil_image.close()
            except (NameError, UnboundLocalError):
                pass
            try:
                del img_array
            except (NameError, UnboundLocalError):
                pass

NODE_CLASS_MAPPINGS = {
    "BasifyDescribeImage": DescribeImage
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyDescribeImage": "Describe Image"
}
