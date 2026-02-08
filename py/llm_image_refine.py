import logging
from typing import Any
import comfy.model_management  # type: ignore[import]
from ..clients.ollama_client import ollama_client

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)
loggerName = f"{Colors.BLUE}BASIFY ImageRefine{Colors.ENDC}"

class ImageRefine:
    """
    Two-stage processing node:
    1. Vision model describes the image
    2. Text model processes the description with user instructions
    """
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("image", "description", "refined_output")
    FUNCTION = "process_image_with_refinement"
    CATEGORY = "basify"
    DESCRIPTION = "Process image with vision model, then refine description with text model"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        all_models: list[str] = ollama_client().models or []  # type: ignore[assignment]
        
        # Create separate lists for vision and text models
        vision_models = [m for m in all_models if any(x in m.lower() for x in ['llava', 'bakllava', 'moondream'])]  # type: ignore[union-attr]
        text_models = [m for m in all_models if not any(x in m.lower() for x in ['llava', 'bakllava', 'moondream'])]  # type: ignore[union-attr]
        
        # Fallback if filtering results in empty lists
        if not vision_models:
            vision_models = all_models[:1] if all_models else ["llava:latest"]  # type: ignore[assignment]
        if not text_models:
            text_models = all_models[1:] if len(all_models) > 1 else all_models if all_models else ["llama3.2:latest"]  # type: ignore[assignment]
        
        return {
            "required": {
                "image": ("IMAGE",),
                "vision_model": (vision_models,),
                "vision_prompt": ("STRING", {
                    "multiline": True,
                    "default": "Describe this image in detail.",
                    "placeholder": "What should the vision model do with the image?"
                }),
                "text_model": (text_models,),
                "text_instructions": ("STRING", {
                    "multiline": True, 
                    "default": "Enhance this description to be more detailed and vivid.",
                    "placeholder": "What should the text model do with the description?"
                }),
            },
            "optional": {
                "vision_temperature": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 2.0, "step": 0.05}),
                "vision_top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
                "vision_top_k": ("INT", {"default": 40, "min": 1, "max": 100, "step": 1}),
                "text_temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.05}),
                "text_presence_penalty": ("INT", {"default": 0, "min": -2, "max": 2, "step": 1}),
                "text_frequency_penalty": ("INT", {"default": 0, "min": -2, "max": 2, "step": 1}),
                "text_top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
                "text_top_k": ("INT", {"default": 40, "min": 1, "max": 100, "step": 1}),
            }
        }

    def process_image_with_refinement(
        self, 
        image: Any,
        vision_model: str,
        vision_prompt: str,
        text_model: str,
        text_instructions: str,
        vision_temperature: float = 0.3,
        vision_top_p: float = 0.95,
        vision_top_k: int = 40,
        text_temperature: float = 0.7,
        text_presence_penalty: int = 0,
        text_frequency_penalty: int = 0,
        text_top_p: float = 0.95,
        text_top_k: int = 40
    ) -> tuple[Any, str, str]:
        """
        Process image through two-stage pipeline:
        1. Vision model generates description
        2. Text model refines description with user instructions
        """
        client = None
        image_description = ""
        refined_output = ""
        
        try:
            logger.info(f"[{loggerName}] {Colors.BLUE}Starting two-stage image processing{Colors.ENDC}")
            logger.info(f"[{loggerName}] {Colors.YELLOW}Vision model selected: {vision_model}{Colors.ENDC}")
            logger.info(f"[{loggerName}] {Colors.YELLOW}Text model selected: {text_model}{Colors.ENDC}")
            logger.info(f"[{loggerName}] {Colors.YELLOW}Vision prompt: '{vision_prompt}'{Colors.ENDC}")
            logger.info(f"[{loggerName}] {Colors.YELLOW}Text instructions: '{text_instructions}'{Colors.ENDC}")
            
            # Force cleanup before processing
            comfy.model_management.unload_all_models()  # type: ignore[attr-defined]
            comfy.model_management.soft_empty_cache(force=True)  # type: ignore[attr-defined]
            
            # Get the image tensor (handle batch)
            if image.dim() == 4:  # Batch dimension
                image_tensor = image[0:1]  # Keep batch dimension but take first image
            else:
                image_tensor = image
            
            # Get client
            client = ollama_client()
            
            # Stage 1: Get image description
            logger.info(f"[{loggerName}] {Colors.YELLOW}Stage 1: Describing image with {vision_model}{Colors.ENDC}")
            
            description_result: str = str(client.process_image(  # type: ignore[union-attr]
                model=vision_model,
                image_tensor=image_tensor,
                temperature=vision_temperature,
                top_p=vision_top_p,
                top_k=vision_top_k,
                custom_system_prompt=vision_prompt if vision_prompt.strip() else None
            ) or "")
            
            # Ensure image_description is always a string
            image_description = description_result if description_result else "Error: No description generated"
            
            if not description_result or description_result.startswith("Error"):
                logger.error(f"[{loggerName}] {Colors.RED}Failed to generate image description{Colors.ENDC}")
                return (image, image_description, "")
            
            logger.info(f"[{loggerName}] {Colors.GREEN}Description generated: {len(image_description)} chars{Colors.ENDC}")
            
            # Stage 2: Refine description with text model  
            logger.info(f"[{loggerName}] {Colors.YELLOW}Stage 2: Refining with {text_model}{Colors.ENDC}")
            
            # Combine the text instructions and description
            second_prompt = f"{text_instructions}\n\n{image_description}"
            
            logger.info(f"[{loggerName}] {Colors.GREEN}Second prompt being sent: {second_prompt[:200]}...{Colors.ENDC}")
            
            refinement_result: str = str(client.process_template(  # type: ignore[union-attr]
                model=text_model,
                user_prompt=second_prompt,
                temperature=text_temperature,
                presence_penalty=text_presence_penalty,
                frequency_penalty=text_frequency_penalty,
                top_p=text_top_p,
                top_k=text_top_k
            ) or "")
            
            # Ensure refined_output is always a string
            refined_output = refinement_result if refinement_result else "Error: Refinement failed"
            
            if not refinement_result or refinement_result.startswith("Error"):
                logger.error(f"[{loggerName}] {Colors.RED}Failed to refine description{Colors.ENDC}")
                return (image, image_description, refined_output)
            
            logger.info(f"[{loggerName}] {Colors.GREEN}Processing complete{Colors.ENDC}")
            
            # Return image passthrough, original description, and refined output
            return (image, image_description, refined_output)
            
        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error in image refinement: {str(e)}{Colors.ENDC}")
            error_msg = f"Error: {str(e)}"
            # Use the initialized variables which may be empty strings
            return (image, image_description if image_description else error_msg, refined_output if refined_output else error_msg)
        finally:
            # Ensure cleanup even on error
            try:
                del image_description
            except (NameError, UnboundLocalError):
                pass
            try:
                del refined_output
            except (NameError, UnboundLocalError):
                pass


NODE_CLASS_MAPPINGS = {
    "BasifyImageRefine": ImageRefine
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyImageRefine": "Basify: Ollama Image Description and Text Transformer"
}
