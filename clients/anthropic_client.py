import os
import json
import random
import logging

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)
loggerName = f"{Colors.BLUE}BASIFY AnthropicAI{Colors.ENDC}"

class AnthropicClient:
    _client = None
    _models = None

    # Remember, 
    #   self is the __instance__ of the class
    #   cls is the __class__ itself

    @property
    def models(self):
        return self._models
    # end models
        
    def __init__(self, api_key):
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("Anthropic package is not installed. Please install it using 'pip install anthropic'")
        
        self._client = Anthropic(api_key=api_key)
        self.filter_models()

    def filter_models(self):
        all_models = None
        filtered_models = None
        
        try:
            if self._models is None:
                try:
                    logger.info(f"[{loggerName}] {Colors.GREEN}Fetching Anthropic models...{Colors.ENDC}")
                    all_models = self._client.models.list()
                    # Filter for relevant GPT models
                    filtered_models = [
                        model.id for model in all_models
                    ]

                    self._models = filtered_models
                    
                    # Clean up intermediate lists
                    del all_models
                    del filtered_models
                    
                    if not self._models:
                        logger.warning(f"[{loggerName}] {Colors.YELLOW}No models found!{Colors.ENDC}")
                        self._models = ["No models found!"]
                        
                except Exception as e:
                    logger.error(f"[{loggerName}] {Colors.RED}Error filtering models: {str(e)}{Colors.ENDC}")
                    self._models = [f"Error filtering models: {str(e)}"]
        finally:
            # Ensure cleanup even on error
            if all_models is not None:
                del all_models
            if filtered_models is not None:
                del filtered_models

    def _load_system_prompt(self, isCreative=True):
        try:
            logger.info(f"[{loggerName}] {Colors.GREEN}Loading system prompt (Creative: {isCreative}){Colors.ENDC}")
            # choose the right file based on isCreative
            filename = 'creative.txt' if isCreative else 'strict.txt'
            prompt_path = os.path.join(os.path.dirname(__file__), '../prompts/' + filename)
            with open(prompt_path, 'r') as file:
                return file.read()
        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error loading system prompt: {str(e)}{Colors.ENDC}")
            raise
    # end _load_system_prompt

    def process_template(self, llm_client, model, template, prompt_style, temperature=1.0, top_p=None, word_limit=75):
        logger.info(f"[{loggerName}] {Colors.GREEN}Processing template with model: {Colors.YELLOW}{model}{Colors.ENDC}")
        system_prompt = self._load_system_prompt(prompt_style)
        system_prompt = system_prompt.replace('%word_limit%', str(word_limit))
        messages = None
        create_params = None
        response = None

        try:
            messages = [
                {"role": "user", "content": template}
            ]

            # Prepare parameters for the API call
            create_params = {
                "model": model,
                "max_tokens": 1024,
                "temperature": temperature,
                "system": system_prompt,
                "messages": messages
            }
            
            # Add top_p if it's provided and not None
            if top_p is not None:
                create_params["top_p"] = top_p
                
            logger.info(f"[{loggerName}] {Colors.GREEN}API parameters: {create_params}{Colors.ENDC}")
            
            response = self._client.messages.create(**create_params)

            # role='assistant', 
            # stop_reason='end_turn', 
            # stop_sequence=None, 
            # type='message', 
            # usage=Usage(cache_creation_input_tokens=0, cache_read_input_tokens=0, input_tokens=587, output_tokens=102))
            logger.info(f"[{loggerName}] {Colors.GREEN}Successfully processed template{Colors.ENDC}")
            
            # Extract result before cleanup
            result = response.content[0].text
            
            # Clean up large objects
            del response
            del create_params
            del messages
            del system_prompt
            
            return result
            
        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error processing template: {str(e)}{Colors.ENDC}")
            return f"Error processing template: {str(e)}"
        finally:
            # Ensure cleanup even on error
            if response is not None:
                del response
            if create_params is not None:
                del create_params
            if messages is not None:
                del messages


_anthropic_client = None
def anthropic_client():
    global _anthropic_client
    if (_anthropic_client is None):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        _anthropic_client = AnthropicClient(api_key)
    return _anthropic_client