import os
import json
import logging

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)
loggerName = f"{Colors.BLUE}BASIFY OpenAI{Colors.ENDC}"

class OpenAIClient:
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
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI package is not installed. Please install it using 'pip install openai'")
        
        self._client = OpenAI(api_key=api_key)
        self.filter_models()
    # end __init__

    def filter_models(self):
        if self._models is None:
            try:
                logger.info(f"[{loggerName}] {Colors.GREEN}Fetching OpenAI models...{Colors.ENDC}")
                all_models = self._client.models.list()
                # Filter for relevant GPT models
                filtered_models = [
                    model.id for model in all_models
                    if (
                        model.id.startswith('gpt') and  # Only GPT models
                        not any(suffix in model.id for suffix in [
                            'instruct',     # Instruction-specific models
                            'audio',        # Audio-specific models
                            'realtime',     # Realtime models
                            '-0',           # Dated versions like gpt-4-0613
                            '-1',           # Dated versions like gpt-4-1106
                            '-2',           # Future dated versions
                            'preview'       # Preview models
                        ])
                    )

                ]

                self._models = filtered_models
                
                if not self._models:
                    logger.warning(f"[{loggerName}] {Colors.YELLOW}No models found!{Colors.ENDC}")
                    self._models = ["No models found!"]
                    
            except Exception as e:
                logger.error(f"[{loggerName}] {Colors.RED}Error filtering models: {str(e)}{Colors.ENDC}")
                self._models = [f"Error filtering models: {str(e)}"]
    # end filter_models

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

    def process_template(self, llm_client, model, template, prompt_style, temperature=1.0, presence_penalty=1.0, frequency_penalty=1.0, top_p=1.0, top_k=None, word_limit=75):
        logger.info(f"[{loggerName}] {Colors.GREEN}Processing template with model: {Colors.YELLOW}{model}{Colors.ENDC}")
        system_prompt = self._load_system_prompt(prompt_style)
        system_prompt = system_prompt.replace('%word_limit%', str(word_limit))

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": template}
        ]

        try:
            # Prepare parameters for the API call
            create_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            
            # Add either presence/frequency penalties or top_p/top_k based on which ones are provided
            if top_p < 1.0:  # If top_p is set (default is 1.0), we're in sampling mode
                create_params["top_p"] = top_p
                # OpenAI doesn't directly support top_k, so we'll skip it
            else:  # Otherwise we're in penalty mode
                create_params["presence_penalty"] = presence_penalty
                create_params["frequency_penalty"] = frequency_penalty
            
            logger.info(f"[{loggerName}] {Colors.GREEN}API parameters: {create_params}{Colors.ENDC}")
            
            response = self._client.chat.completions.create(**create_params)
            logger.info(f"[{loggerName}] {Colors.GREEN}Successfully processed template{Colors.ENDC}")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error processing template: {str(e)}{Colors.ENDC}")
            return f"Error processing template: {str(e)}"
    # end process_template
# end OpenAIClient

_openai_client = None
def openai_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _openai_client = OpenAIClient(api_key)
    return _openai_client