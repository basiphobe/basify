import os
import logging

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)
loggerName = f"{Colors.BLUE}BASIFY VertexAI{Colors.ENDC}"

class VertexAIClient:
    _client = None
    _models = None
    _project = "llmlibs"
    _location = "us-central1"
    _parent = f"projects/{_project}/locations/{_location}"

    # Remember, 
    #   self is the __instance__ of the class
    #   cls is the __class__ itself

    @property
    def models(self):
        return self._models
    # end models
        
    def __init__(self):
        try:
            from google.cloud import aiplatform
        except ImportError:
            raise ImportError("Anthropic package is not installed. Please install it using 'pip install anthropic'")
        
        aiplatform.init(project=self._project, location=self._location)
        self._client = aiplatform.ModelServiceClient()

    def filter_models(self):
        request = None
        all_models = None
        filtered_models = None
        
        try:
            if self._models is None:
                try:
                    logger.info(f"[{loggerName}] {Colors.GREEN}Fetching VertexAI models...{Colors.ENDC}")
                    
                    request = self._client.ListModelsRequest(parent=self._parent)
                    all_models = self._client.list_models(request=request)
                    # Filter for relevant GPT models
                    filtered_models = [
                        model.display_name for model in all_models
                    ]

                    self._models = filtered_models
                    
                    # Clean up intermediate objects
                    del request
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
            if request is not None:
                del request
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
            logger.error(f"Error loading system prompt: {str(e)}")
            raise
    # end _load_system_prompt                

    def process_template(self, llm_client, model, template, prompt_style, temperature=1.0, presence_penalty=0.0, frequency_penalty=0.0, top_p=1.0, top_k=40, word_limit=75):
        logger.info(f"[{loggerName}] {Colors.GREEN}Processing template with model: {Colors.YELLOW}{model}{Colors.ENDC}")
        system_prompt = self._load_system_prompt(prompt_style)
        system_prompt = system_prompt.replace('%word_limit%', str(word_limit))
        params = None

        try:
            # Build parameters based on which mode is being used
            params = {
                "temperature": temperature,
            }
            
            # Add the appropriate parameters based on which ones are provided
            if top_p < 1.0:  # If top_p is set (not default), use sampling mode
                params["top_p"] = top_p
                params["top_k"] = top_k
            else:  # Otherwise use penalty mode
                params["presence_penalty"] = presence_penalty
                params["frequency_penalty"] = frequency_penalty
                
            # This is a placeholder since the actual API implementation is not complete
            logger.info(f"[{loggerName}] {Colors.GREEN}API parameters: {params}{Colors.ENDC}")
            
            # Clean up before returning
            del system_prompt
            del params
            
            return ""
            
        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error processing template: {str(e)}{Colors.ENDC}")
            return f"Error processing template: {str(e)}"
        finally:
            # Ensure cleanup even on error
            if params is not None:
                del params

_vertexai_client = None
def vertexai_client():
    global _vertexai_client
    if (_vertexai_client is None):
        _vertexai_client = VertexAIClient()
    return _vertexai_client