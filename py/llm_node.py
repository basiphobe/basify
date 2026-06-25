import logging
import re
from typing import Any
from . import llm_service_registry as registry

# Pattern to match <think>...</think> blocks from reasoning models
_THINK_PATTERN = re.compile(r'<think>.*?</think>\s*', flags=re.DOTALL)

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'

logger = logging.getLogger(__name__)
loggerName = f"{Colors.BLUE}BASIFY LLMProcess{Colors.ENDC}"


class LLMProcess:
    """
    Universal LLM text processing node.
    Supports any OpenAI-compatible API (Ollama, OpenAI, LM Studio, Groq, etc.)
    and Anthropic via a JSON service registry.
    """
    RETURN_TYPES = ("STRING",)
    FUNCTION = "process"
    CATEGORY = "basify"
    DESCRIPTION = "Process text through any configured LLM service (Ollama, OpenAI, Anthropic, etc.)"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        services = registry.get_service_names()
        if not services:
            services = ["No services configured"]

        return {
            "required": {
                "service": (services, {"default": services[0]}),
                "model": ("STRING", {"default": "Select a service first", "placeholder": "Model will be populated dynamically"}),
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "System instructions: how should the AI behave?"
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Enter your prompt here..."
                }),
            },
            "optional": {
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.05}),
                "max_tokens": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
                "top_k": ("INT", {"default": 40, "min": 1, "max": 100, "step": 1}),
            }
        }

    def process(
        self,
        service: str,
        model: str,
        system_prompt: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        top_k: int = 40,
    ) -> tuple[str]:
        """Process the input through the selected LLM service."""
        try:
            logger.info(f"[{loggerName}] {Colors.YELLOW}Calling {service} / {model}{Colors.ENDC}")

            response = registry.call(
                service_name=service,
                model=model,
                system_prompt=system_prompt,
                user_prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
            )

            # Strip <think>...</think> blocks from reasoning models
            response = _THINK_PATTERN.sub('', response).strip()

            # Also strip unclosed <think> blocks (model ran out of context mid-thought)
            if response.startswith('<think>'):
                response = ''

            if not response:
                return ("Error: Model produced no output (likely spent entire context on reasoning). Use a non-thinking model or increase OLLAMA_NUM_CTX.",)

            logger.info(f"[{loggerName}] {Colors.GREEN}Response received ({len(response)} chars){Colors.ENDC}")
            return (response,)

        except Exception as e:
            logger.error(f"[{loggerName}] {Colors.RED}Error: {e}{Colors.ENDC}")
            return (f"Error: {str(e)}",)


NODE_CLASS_MAPPINGS = {
    "LLMProcess": LLMProcess
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LLMProcess": "Basify: LLM Process"
}
