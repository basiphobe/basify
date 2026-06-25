import os
import json
import logging
import requests
from typing import Any

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'

logger = logging.getLogger(__name__)
loggerName = f"{Colors.BLUE}BASIFY LLMRegistry{Colors.ENDC}"

# Path to the services config file
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'llm_services.json')


def _load_config() -> list[dict[str, Any]]:
    """Re-read llm_services.json on every call (hot-reload)."""
    try:
        with open(_CONFIG_PATH, 'r') as f:
            data = json.load(f)
        return data.get("services", [])
    except Exception as e:
        logger.error(f"[{loggerName}] {Colors.RED}Error loading llm_services.json: {e}{Colors.ENDC}")
        return []


def _get_service_config(service_name: str) -> dict[str, Any] | None:
    """Find a service entry by name."""
    services = _load_config()
    for svc in services:
        if svc.get("name") == service_name:
            return svc
    return None


def _get_api_key(service: dict[str, Any]) -> str:
    """Resolve the API key from env var or default."""
    env_var = service.get("api_key_env", "")
    key = os.environ.get(env_var, "") if env_var else ""
    if not key:
        key = service.get("api_key_default") or ""
    return key


# Client cache: keyed by (service_name, type)
_client_cache: dict[str, Any] = {}


def get_service_names() -> list[str]:
    """Return all configured service names (re-reads config each time)."""
    services = _load_config()
    return [svc["name"] for svc in services if "name" in svc]


def get_models(service_name: str) -> list[str]:
    """Fetch the model list for a given service. Returns graceful error on failure."""
    service = _get_service_config(service_name)
    if not service:
        return [f"Error: Service '{service_name}' not found in llm_services.json"]

    svc_type = service.get("type", "openai_compatible")
    api_key = _get_api_key(service)

    if not api_key:
        env_var = service.get("api_key_env", "")
        return [f"Error: {env_var} environment variable not set"]

    try:
        if svc_type == "openai_compatible":
            return _get_models_openai(service, api_key)
        elif svc_type == "anthropic":
            return _get_models_anthropic(service, api_key)
        else:
            return [f"Error: Unknown service type '{svc_type}'"]
    except Exception as e:
        logger.error(f"[{loggerName}] {Colors.RED}Error fetching models for {service_name}: {e}{Colors.ENDC}")
        return [f"Service unavailable: {str(e)[:80]}"]


def _get_models_openai(service: dict[str, Any], api_key: str) -> list[str]:
    """Fetch models from an OpenAI-compatible endpoint."""
    base_url = service.get("base_url", "").rstrip("/")
    model_filter = service.get("model_filter")

    try:
        from openai import OpenAI
    except ImportError:
        return ["Error: openai package not installed (pip install openai)"]

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=5.0)

    models_response = client.models.list()
    model_ids = [m.id for m in models_response]

    if model_filter:
        model_ids = [m for m in model_ids if model_filter.lower() in m.lower()]

    model_ids.sort()
    return model_ids if model_ids else ["No models found"]


def _get_models_anthropic(service: dict[str, Any], api_key: str) -> list[str]:
    """Fetch models from Anthropic's API."""
    try:
        from anthropic import Anthropic
    except ImportError:
        return ["Error: anthropic package not installed (pip install anthropic)"]

    client = Anthropic(api_key=api_key, timeout=5.0)

    try:
        models_response = client.models.list()
        model_ids = [m.id for m in models_response]
    except Exception:
        # Fallback: Anthropic model list API may not be available on all plans
        model_ids = [
            "claude-sonnet-4-20250514",
            "claude-haiku-4-20250414",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]

    model_filter = service.get("model_filter")
    if model_filter:
        model_ids = [m for m in model_ids if model_filter.lower() in m.lower()]

    model_ids.sort()
    return model_ids if model_ids else ["No models found"]


def call(
    service_name: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    top_p: float = 0.95,
    top_k: int = 40,
) -> str:
    """
    Dispatch a completion call to the appropriate service.
    Handles VRAM management for local services.
    """
    service = _get_service_config(service_name)
    if not service:
        return f"Error: Service '{service_name}' not found in llm_services.json"

    svc_type = service.get("type", "openai_compatible")
    api_key = _get_api_key(service)
    is_local = service.get("local", False)

    if not api_key:
        env_var = service.get("api_key_env", "")
        return f"Error: {env_var} environment variable not set"

    # For local services: free ComfyUI VRAM before the LLM call
    if is_local:
        try:
            import comfy.model_management  # type: ignore[import]
            comfy.model_management.unload_all_models()
            comfy.model_management.soft_empty_cache(force=True)
            logger.info(f"[{loggerName}] {Colors.YELLOW}Unloaded ComfyUI models for local LLM call{Colors.ENDC}")
        except Exception as e:
            logger.warning(f"[{loggerName}] {Colors.YELLOW}Could not unload ComfyUI models: {e}{Colors.ENDC}")

    try:
        if svc_type == "openai_compatible":
            result = _call_openai(service, api_key, model, system_prompt, user_prompt, temperature, max_tokens, top_p, top_k)
        elif svc_type == "anthropic":
            result = _call_anthropic(service, api_key, model, system_prompt, user_prompt, temperature, max_tokens, top_p)
        else:
            result = f"Error: Unknown service type '{svc_type}'"
    except Exception as e:
        logger.error(f"[{loggerName}] {Colors.RED}Error calling {service_name}: {e}{Colors.ENDC}")
        result = f"Error: {str(e)}"
    finally:
        # For local services: unload the LLM model to free VRAM back for ComfyUI
        if is_local:
            _unload_local_model(service, model)

    return result


def _call_openai(
    service: dict[str, Any],
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    top_k: int,
) -> str:
    """Call an OpenAI-compatible API."""
    try:
        from openai import OpenAI, BadRequestError
    except ImportError:
        return "Error: openai package not installed (pip install openai)"

    base_url = service.get("base_url", "").rstrip("/")
    client = OpenAI(api_key=api_key, base_url=base_url)

    messages: list[dict[str, str]] = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    create_params: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False,
    }

    # OpenAI's newer models require max_completion_tokens instead of max_tokens.
    # Other OpenAI-compatible APIs (Ollama, LM Studio, etc.) still use max_tokens.
    is_openai_official = "api.openai.com" in base_url
    if is_openai_official:
        create_params["max_completion_tokens"] = max_tokens
    else:
        create_params["max_tokens"] = max_tokens

    # Some models (reasoning models like o1, o3, gpt-5-mini) don't support
    # temperature/top_p. If any sampling param is rejected, strip them all and retry.
    try:
        response = client.chat.completions.create(**create_params)
    except BadRequestError as e:
        error_msg = str(e).lower()
        if "temperature" in error_msg or "top_p" in error_msg or "unsupported_parameter" in error_msg:
            # Reasoning models reject all sampling params — strip them all at once
            create_params.pop("temperature", None)
            create_params.pop("top_p", None)
            logger.info(f"[{loggerName}] {Colors.YELLOW}Retrying without sampling params for {model}{Colors.ENDC}")
            response = client.chat.completions.create(**create_params)
        elif "max_tokens" in error_msg or "max_completion_tokens" in error_msg:
            create_params.pop("max_tokens", None)
            create_params.pop("max_completion_tokens", None)
            logger.info(f"[{loggerName}] {Colors.YELLOW}Retrying without max_tokens for {model}{Colors.ENDC}")
            response = client.chat.completions.create(**create_params)
        else:
            raise

    content = response.choices[0].message.content if response.choices else ""
    return content or ""


def _call_anthropic(
    service: dict[str, Any],
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
) -> str:
    """Call Anthropic's API."""
    try:
        from anthropic import Anthropic
    except ImportError:
        return "Error: anthropic package not installed (pip install anthropic)"

    client = Anthropic(api_key=api_key)

    create_params: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    if system_prompt.strip():
        create_params["system"] = system_prompt

    response = client.messages.create(**create_params)
    content = response.content[0].text if response.content else ""
    return content or ""


def _unload_local_model(service: dict[str, Any], model: str) -> None:
    """
    Unload a local LLM model from VRAM.
    For Ollama: POST /api/generate with keep_alive=0.
    For other local services: attempt the same pattern.
    """
    try:
        # Derive the base Ollama URL from the OpenAI-compatible URL
        # e.g. http://127.0.0.1:11434/v1 → http://127.0.0.1:11434
        base_url = service.get("base_url", "").rstrip("/")
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]

        unload_url = f"{base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": "",
            "keep_alive": 0,
        }
        requests.post(unload_url, json=payload, timeout=5)
        logger.info(f"[{loggerName}] {Colors.GREEN}Unloaded local model: {model}{Colors.ENDC}")
    except Exception as e:
        logger.warning(f"[{loggerName}] {Colors.YELLOW}Could not unload local model {model}: {e}{Colors.ENDC}")
