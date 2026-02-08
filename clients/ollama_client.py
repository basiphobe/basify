import os
import logging
import re
import comfy.model_management

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)
loggerName = f"{Colors.BLUE}BASIFY Ollama{Colors.ENDC}"

class OllamaClient:
    _client = None
    _models = None

    @property
    def models(self):
        return self._models

    def __init__(self, base_url):
        try:
            from ollama import Client
        except ImportError:
            raise ImportError("Ollama package is not installed. Please install it using 'pip install ollama'")

        self._client = Client(host=base_url)
        self.filter_models()

    def filter_models(self):
        all_models = None
        filtered_models = None
        
        try:
            if self._models is None:
                try:
                    all_models = self._client.list()
                    filtered_models = [
                        model.model for model in all_models.models
                    ]

                    self._models = sorted(filtered_models, key=str.casefold)

                    if not self._models:
                        logger.warning(f"[{loggerName}] {Colors.YELLOW}No models found!{Colors.ENDC}")
                        self._models = ["No models found!"]

                except Exception as e:
                    logger.error(f"[{loggerName}] {Colors.RED}Error filtering models: {str(e)}{Colors.ENDC}")
                    self._models = [f"Error filtering models: {str(e)}"]
        finally:
            # Ensure cleanup even on error
            try:
                del all_models
            except (NameError, UnboundLocalError):
                pass
            try:
                del filtered_models
            except (NameError, UnboundLocalError):
                pass

    def parse_model_info(self, model_info: dict) -> dict:
        details_dict = None
        model_info_dict = None
        parameters_dict = None
        
        try:
            # Extract details object attributes
            details = model_info.get('details', {})
            details_dict = {
                'parent_model': details.parent_model if details else '',
                'format': details.format if details else '',
                'family': details.family if details else '',
                'parameter_size': details.parameter_size if details else '',
                'quantization_level': details.quantization_level if details else ''
            }

            # Extract modelinfo dictionary
            model_info_dict = model_info.get('modelinfo', {})

            # Parse parameters string into dictionary
            parameters_str = model_info.get('parameters', '')
            parameters_dict = {}
            if parameters_str:
                for line in parameters_str.split('\n'):
                    parts = line.strip().split(None, 1)
                    if len(parts) == 2:
                        key, value = parts
                        parameters_dict[key] = value.strip('"')

            # Format datetime object to ISO format string
            modified_at = model_info.get('modified_at')
            modified_at_str = modified_at.isoformat() if modified_at else ''

            # Combine all information (excluding modelfile)
            parsed_info = {
                'modified_at': modified_at_str,
                'template': model_info.get('template', '').strip("'"),
                'details': details_dict,
                'modelinfo': model_info_dict,
                'parameters': parameters_dict
            }
            
            # Clean up intermediate dicts (they're now in parsed_info)
            del details_dict
            del model_info_dict
            del parameters_dict

            return parsed_info

        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error parsing model information: {str(e)}{Colors.ENDC}")
            return {}
        finally:
            # Ensure cleanup even on error
            try:
                del details_dict
            except (NameError, UnboundLocalError):
                pass
            try:
                del model_info_dict
            except (NameError, UnboundLocalError):
                pass
            try:
                del parameters_dict
            except (NameError, UnboundLocalError):
                pass
        
    def get_model_information(self, model_name):
        try:
            model_info = self._client.show(model_name)
            return self.parse_model_info(model_info)
        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error fetching model information: {str(e)}{Colors.ENDC}")
            return None

    def _load_system_prompt(self, prompt_assistant='Strict'):
        try:
            # Use default if None is passed
            if prompt_assistant is None:
                prompt_assistant = 'Strict'
            filename = f'{prompt_assistant.lower()}.txt'
            prompt_path = os.path.join(os.path.dirname(__file__), '../../js/assistants/' + filename)
            with open(prompt_path, 'r') as file:
                return file.read()
        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error loading assistant: {str(e)}{Colors.ENDC}")
            raise

    def unload_model(self, model_name):
        payload = None
        response = None
        
        try:
            # Force cleanup
            comfy.model_management.unload_all_models()
            comfy.model_management.soft_empty_cache(force=True)

            logger.info(f"{loggerName} {Colors.BLUE}Unloading model: {model_name} from memory{Colors.ENDC}")
            
            # Prepare the unload request payload
            payload = {
                "model": model_name,
                "prompt": "",
                "keep_alive": 0
            }
            
            # Call the Ollama API to unload the model
            response = self._client.generate(**payload)

            logger.info(f"{loggerName} {Colors.BLUE}Successfully unloaded model: {model_name}{Colors.ENDC}")
            
            return True
        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error unloading model {model_name}: {str(e)}{Colors.ENDC}")
            return False
        finally:
            # Ensure cleanup even on error
            try:
                del payload
            except (NameError, UnboundLocalError):
                pass
            try:
                del response
            except (NameError, UnboundLocalError):
                pass
        
    def format_model_prompt(self, template, system_prompt, user_prompt):
        context = None
        
        try:
            # Create a context dict with our available variables
            context = {
                "System": system_prompt,
                "Prompt": user_prompt,
                "Response": "",  # Empty for initial prompt
                "Messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            
            # Use the template directly if it exists
            if template:
                try:
                    # Handle message-based templates (iterate through messages)
                    if "{{- range" in template:
                        # Template uses message format - return as is since Ollama will handle it
                        return template
                    
                    # Handle simple variable replacement
                    formatted = template
                    for key, value in context.items():
                        if isinstance(value, str):
                            # Replace both {{ .Key }} and {{ .key }} patterns
                            formatted = re.sub(r'{{\s*\.' + key + r'\s*}}', str(value), formatted)
                            formatted = re.sub(r'{{\s*\.' + key.lower() + r'\s*}}', str(value), formatted)
                    
                    # Clean up before returning
                    del context
                    
                    return formatted
                    
                except Exception as e:
                    logger.error(f"[{loggerName}] {Colors.RED}Error formatting prompt with template: {str(e)}{Colors.ENDC}")
                    # Fallback to basic format if template processing fails
                    return f"{system_prompt}\n{user_prompt}"
            
            # Fallback for no template
            return f"{system_prompt}\n{user_prompt}"
        finally:
            # Ensure cleanup even on error
            try:
                del context
            except (NameError, UnboundLocalError):
                pass    

    def process_template(self, model, user_prompt, temperature=0.3, presence_penalty=0, frequency_penalty=0, top_p=0.95, top_k=40, prompt_assistant=None, system_prompt=None):
        model_info = None
        options = None
        generate_args = None
        response = None
        
        try:
            # Force cleanup before loading new model
            comfy.model_management.unload_all_models()
            comfy.model_management.soft_empty_cache(force=True)
            
            # Only load assistant if explicitly requested and no system_prompt provided
            if system_prompt is None and prompt_assistant is not None:
                system_prompt = self._load_system_prompt(prompt_assistant)
            
            model_info = self.get_model_information(model)
            
            # Build the options dictionary based on the parameters provided
            options = {
                "temperature": temperature,
            }
            
            # Add either presence/frequency penalties or top_p/top_k based on which parameters are being used
            if top_p < 1.0:  # If top_p is set (not default), we're in sampling mode
                options["top_p"] = top_p
                options["top_k"] = top_k
            else:  # Otherwise we're in penalty mode
                options["presence_penalty"] = presence_penalty
                options["frequency_penalty"] = frequency_penalty

            generate_args = {
                "model": model,
                "prompt": user_prompt,
                "stream": False,
                "options": options
            }
            
            # Only add system prompt if provided
            if system_prompt:
                generate_args["system"] = system_prompt

            logger.info(f"[{loggerName}] {Colors.YELLOW}generate_args: {generate_args}{Colors.ENDC}")

            if model_info and model_info.get('template'):
                generate_args["template"] = model_info['template']
            else:
                logger.warning(f"[{loggerName}] {Colors.YELLOW}No template available, using basic format{Colors.ENDC}")

            logger.info(f"[{loggerName}] {Colors.YELLOW}Generating response with: {generate_args}{Colors.ENDC}")

            response = self._client.generate(**generate_args)
            
            comfy.model_management.soft_empty_cache(force=True)

            if not response or not response.response:
                logger.error(f"[{loggerName}] {Colors.RED}Empty response received from model{Colors.ENDC}")
                logger.error(f"[{loggerName}] {Colors.RED}Response: {generate_args}{Colors.ENDC}")
                return "Error: Empty response from model. Check server logs."
            
            # Extract result before cleanup
            result = response.response
                
            # Always unload the model after processing
            self.unload_model(model)
            
            # Clean up large objects
            del response
            del generate_args
            del options
            del model_info
            
            return result

        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error in process_template: {str(e)}{Colors.ENDC}")
            return f"Error processing template: {str(e)}"
        finally:
            # Ensure cleanup even on error
            try:
                del response
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
            try:
                del model_info
            except (NameError, UnboundLocalError):
                pass

    def process_image(self, model, image_tensor, temperature=0.3, top_p=0.95, top_k=40, prompt_assistant=None, custom_system_prompt=None):
        image_np = None
        pil_image = None
        buffer = None
        base64_image = None
        system_prompt = None
        model_info = None
        options = None
        generate_args = None
        response = None
        
        try:
            import io
            import base64
            from PIL import Image
            import numpy as np
            
            # Force cleanup before loading new model
            comfy.model_management.unload_all_models()
            comfy.model_management.soft_empty_cache(force=True)
            
            # Convert tensor to PIL image
            if image_tensor.dim() == 4:  # Batch dimension
                image_tensor = image_tensor[0]  # Take first image from batch
            
            # Convert from [H, W, C] to numpy array
            image_np = image_tensor.cpu().numpy()
            
            # Ensure values are in [0, 255] range
            if image_np.max() <= 1.0:
                image_np = (image_np * 255).astype(np.uint8)
            else:
                image_np = image_np.astype(np.uint8)
            
            # Create PIL image
            pil_image = Image.fromarray(image_np)
            
            # Convert to base64
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Close PIL image and buffer immediately after encoding
            pil_image.close()
            buffer.close()
            del pil_image
            del buffer
            del image_np
            pil_image = None
            buffer = None
            image_np = None
            
            # Use custom system prompt if provided, otherwise load from file
            if custom_system_prompt and custom_system_prompt.strip():
                system_prompt = custom_system_prompt
            else:
                system_prompt = self._load_system_prompt(prompt_assistant)
            model_info = self.get_model_information(model)
            
            # Build the options dictionary
            options = {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k
            }

            generate_args = {
                "model": model,
                "prompt": "Describe what you see in this image.",
                "system": system_prompt,
                "images": [base64_image],
                "stream": False,
                "options": options
            }

            logger.info(f"[{loggerName}] {Colors.YELLOW}Processing image with model: {model}{Colors.ENDC}")

            response = self._client.generate(**generate_args)
            
            logger.info(f"[{loggerName}] {Colors.GREEN}Raw response received: {response}{Colors.ENDC}")
            logger.info(f"[{loggerName}] {Colors.GREEN}Response text: {response.response if response else 'None'}{Colors.ENDC}")
            
            comfy.model_management.soft_empty_cache(force=True)

            if not response or not response.response:
                logger.error(f"[{loggerName}] {Colors.RED}Empty response received from model{Colors.ENDC}")
                return "Error: Empty response from model. Check server logs."
            
            # Clean up the response text - strip whitespace and ensure it's a proper string
            cleaned_response = response.response.strip() if response.response else ""
            logger.info(f"[{loggerName}] {Colors.GREEN}Returning cleaned response: '{cleaned_response}'{Colors.ENDC}")
                
            # Always unload the model after processing
            self.unload_model(model)
            
            # Clean up large objects (finally block will handle base64_image)
            result = cleaned_response
            
            del response
            del generate_args
            del options
            del model_info
            del system_prompt
            
            return result

        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error in process_image: {str(e)}{Colors.ENDC}")
            return f"Error processing image: {str(e)}"
        finally:
            # Ensure cleanup even on error
            try:
                if pil_image is not None:
                    pil_image.close()
                del pil_image
            except (NameError, UnboundLocalError):
                pass
            try:
                if buffer is not None:
                    buffer.close()
                del buffer
            except (NameError, UnboundLocalError):
                pass
            try:
                del image_np
            except (NameError, UnboundLocalError):
                pass
            try:
                del base64_image
            except (NameError, UnboundLocalError):
                pass
            try:
                del response
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
            try:
                del model_info
            except (NameError, UnboundLocalError):
                pass
            try:
                del system_prompt
            except (NameError, UnboundLocalError):
                pass

    def process_image_with_text_refinement(
        self, 
        image_tensor, 
        vision_model, 
        text_model,
        user_instructions,
        vision_temperature=0.3,
        vision_top_p=0.95, 
        vision_top_k=40,
        text_temperature=0.7,
        text_presence_penalty=0,
        text_frequency_penalty=0,
        text_top_p=0.95,
        text_top_k=40,
        vision_prompt_assistant=None,
        text_prompt_assistant=None,
        custom_vision_prompt=None
    ):
        """
        Two-stage processing: 
        1. Vision model describes the image
        2. Text model processes the description with user instructions
        
        Args:
            image_tensor: Input image tensor
            vision_model: Model name for image description
            text_model: Model name for text processing
            user_instructions: User-provided processing instructions
            vision_temperature: Temperature for vision model (default: 0.3)
            vision_top_p: Top-p for vision model (default: 0.95)
            vision_top_k: Top-k for vision model (default: 40)
            text_temperature: Temperature for text model (default: 0.7)
            text_presence_penalty: Presence penalty for text model (default: 0)
            text_frequency_penalty: Frequency penalty for text model (default: 0)
            text_top_p: Top-p for text model (default: 0.95)
            text_top_k: Top-k for text model (default: 40)
            vision_prompt_assistant: Assistant preset for vision stage
            text_prompt_assistant: Assistant preset for text stage
            custom_vision_prompt: Custom system prompt for vision stage
            
        Returns:
            Final processed text from the two-stage pipeline
        """
        image_description = None
        final_result = None
        
        try:
            logger.info(f"[{loggerName}] {Colors.BLUE}Starting two-stage processing pipeline{Colors.ENDC}")
            
            # Stage 1: Get image description from vision model
            logger.info(f"[{loggerName}] {Colors.YELLOW}Stage 1: Generating image description with {vision_model}{Colors.ENDC}")
            
            image_description = self.process_image(
                model=vision_model,
                image_tensor=image_tensor,
                temperature=vision_temperature,
                top_p=vision_top_p,
                top_k=vision_top_k,
                prompt_assistant=vision_prompt_assistant,
                custom_system_prompt=custom_vision_prompt
            )
            
            if not image_description or image_description.startswith("Error"):
                logger.error(f"[{loggerName}] {Colors.RED}Failed to generate image description{Colors.ENDC}")
                return image_description  # Return error message
            
            logger.info(f"[{loggerName}] {Colors.GREEN}Image description generated: {image_description[:100]}...{Colors.ENDC}")
            
            # Stage 2: Process description with text model
            logger.info(f"[{loggerName}] {Colors.YELLOW}Stage 2: Processing description with {text_model}{Colors.ENDC}")
            
            # Combine description and user instructions into a coherent prompt
            combined_prompt = f"""Image Description:
{image_description}

Instructions:
{user_instructions}

Please process the above image description according to the provided instructions."""
            
            logger.info(f"[{loggerName}] {Colors.YELLOW}Combined prompt: {combined_prompt[:200]}...{Colors.ENDC}")
            
            final_result = self.process_template(
                model=text_model,
                user_prompt=combined_prompt,
                temperature=text_temperature,
                presence_penalty=text_presence_penalty,
                frequency_penalty=text_frequency_penalty,
                top_p=text_top_p,
                top_k=text_top_k,
                prompt_assistant=text_prompt_assistant
            )
            
            if not final_result or final_result.startswith("Error"):
                logger.error(f"[{loggerName}] {Colors.RED}Failed to process description{Colors.ENDC}")
                return final_result  # Return error message
            
            logger.info(f"[{loggerName}] {Colors.GREEN}Two-stage processing complete{Colors.ENDC}")
            
            # Clean up before returning
            result_to_return = final_result
            del image_description
            del final_result
            
            return result_to_return
            
        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error in two-stage processing: {str(e)}{Colors.ENDC}")
            return f"Error in two-stage processing: {str(e)}"
        finally:
            # Ensure cleanup even on error
            try:
                del image_description
            except (NameError, UnboundLocalError):
                pass
            try:
                del final_result
            except (NameError, UnboundLocalError):
                pass
        
_ollama_client = None

def ollama_client():
    global _ollama_client
    if _ollama_client is None:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        _ollama_client = OllamaClient(base_url=base_url)
    return _ollama_client