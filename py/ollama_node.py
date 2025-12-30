import os
import logging
import comfy.model_management
from ..clients.ollama_client import ollama_client

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)
loggerName = f"{Colors.BLUE}BASIFY OllamaNode{Colors.ENDC}"

class OllamaProcess:
    """
    A simple node that takes a string input, processes it with Ollama, and returns the response as a string.
    """
    RETURN_TYPES = ("STRING",)
    FUNCTION = "process_text"
    CATEGORY = "basify"
    DESCRIPTION = "Process text through an Ollama model and return the response."
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        models = ollama_client().models
        
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "placeholder": "Enter text to process..."}),
                "model": (models, {"default": models[0] if models else "No models found!"}),
                "system_prompt": ("STRING", {
                    "multiline": True, 
                    "default": "You are a helpful assistant. Provide clear, accurate, and helpful responses to user queries.",
                    "placeholder": "Enter system instructions for how the AI should respond..."
                }),
                "temperature": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 2.0, "step": 0.05}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
                "top_k": ("INT", {"default": 40, "min": 1, "max": 100, "step": 1}),
            }
        }

    def process_text(self, text, model, system_prompt, temperature, top_p, top_k):
        """Process the input text through Ollama and return the result."""
        client = None
        options = None
        generate_args = None
        response_obj = None
        
        try:
            logger.info(f"[{loggerName}] Processing text with model: {model}")
            
            # Force cleanup before processing
            comfy.model_management.unload_all_models()
            comfy.model_management.soft_empty_cache(force=True)
            
            # Get client once
            client = ollama_client()
            
            # Build options for the model
            options = {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k
            }
            
            generate_args = {
                "model": model,
                "prompt": text,
                "system": system_prompt,
                "stream": False,
                "options": options
            }
            
            logger.info(f"[{loggerName}] {Colors.YELLOW}Processing with model: {model}{Colors.ENDC}")
            
            response_obj = client._client.generate(**generate_args)
            response = response_obj.response if response_obj else "No response received"
            
            # Don't delete here - let finally block handle cleanup
            
            # Unload model and cleanup after processing
            client.unload_model(model)
            logger.info(f"[{loggerName}] {Colors.GREEN}Text processed successfully{Colors.ENDC}")
            
            return (response,)
            
        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error processing text: {str(e)}{Colors.ENDC}")
            return (f"Error processing text: {str(e)}",)
        finally:
            # Ensure cleanup even on error - use try/except since del removes from namespace
            try:
                del response_obj
            except (NameError, UnboundLocalError):
                pass
            try:
                del generate_args
            except (NameError, UnboundLocalError):
                pass
            try:
                del options
            except (NameError, UnboundLocalError):
                pass


NODE_CLASS_MAPPINGS = {
    "OllamaProcess": OllamaProcess
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OllamaProcess": "Ollama Text Processing"
}
