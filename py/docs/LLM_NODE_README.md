# Basify: LLM Process

A universal LLM text processing node for ComfyUI that supports any OpenAI-compatible API (Ollama, OpenAI, LM Studio, Groq, Together AI, etc.) and Anthropic — all configurable via a JSON file with no code changes needed.

## Features

- **Multi-service support** via JSON config (`llm_services.json`)
- **Two adapter types**: `openai_compatible` (covers 90%+ of providers) and `anthropic`
- **Dynamic model listing** — dropdown populated from the service's API
- **VRAM management** — automatically unloads ComfyUI models before local LLM calls, unloads the LLM after
- **Thinking model support** — strips `<think>...</think>` blocks from reasoning models
- **Resilient API calls** — retries without unsupported parameters (e.g., temperature on reasoning models)
- **Hot-reload config** — edit `llm_services.json` without restarting ComfyUI

## Installation

Requires `openai` and `anthropic` Python packages:

```bash
pip install openai anthropic
```

## Configuration

Edit `llm_services.json` in the package root to add/remove services:

```json
{
  "services": [
    {
      "name": "ollama",
      "type": "openai_compatible",
      "base_url": "http://127.0.0.1:11434/v1",
      "api_key_env": "OLLAMA_API_KEY",
      "api_key_default": "ollama",
      "model_filter": null,
      "local": true
    },
    {
      "name": "openai",
      "type": "openai_compatible",
      "base_url": "https://api.openai.com/v1",
      "api_key_env": "OPENAI_API_KEY",
      "api_key_default": null,
      "model_filter": "gpt",
      "local": false
    },
    {
      "name": "anthropic",
      "type": "anthropic",
      "base_url": "https://api.anthropic.com",
      "api_key_env": "ANTHROPIC_API_KEY",
      "api_key_default": null,
      "model_filter": null,
      "local": false
    }
  ]
}
```

### Service Config Fields

| Field | Description |
|-------|-------------|
| `name` | Display name in the dropdown |
| `type` | `openai_compatible` or `anthropic` |
| `base_url` | API endpoint URL |
| `api_key_env` | Environment variable name for the API key |
| `api_key_default` | Fallback key value (e.g., `"ollama"` for local Ollama) |
| `model_filter` | Optional prefix filter for model listing (e.g., `"gpt"`) |
| `local` | When `true`, unloads ComfyUI VRAM before call and unloads LLM after |

### Adding a New Service

To add LM Studio, Groq, Together AI, etc., just add a JSON entry:

```json
{
  "name": "groq",
  "type": "openai_compatible",
  "base_url": "https://api.groq.com/openai/v1",
  "api_key_env": "GROQ_API_KEY",
  "api_key_default": null,
  "model_filter": null,
  "local": false
}
```

No code changes or restart needed — the config is re-read on each access.

## Inputs

| Input | Type | Description |
|-------|------|-------------|
| `service` | COMBO | Select from configured services |
| `model` | COMBO | Dynamically populated model list |
| `system_prompt` | STRING (multiline) | System instructions — how the AI should behave |
| `prompt` | STRING (multiline) | User prompt — what to generate |
| `temperature` | FLOAT | Sampling temperature (0.0–2.0, default 0.7) |
| `max_tokens` | INT | Maximum response length (64–8192, default 1024) |
| `top_p` | FLOAT | Nucleus sampling (0.0–1.0, default 0.95) |
| `top_k` | INT | Top-K sampling (1–100, default 40) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| `STRING` | STRING | The LLM's response text |

## VRAM Management (Local Services)

When `"local": true` is set for a service:

1. **Before the LLM call**: ComfyUI diffusion models are unloaded from VRAM (`unload_all_models()` + `soft_empty_cache()`)
2. **After the LLM call**: The local LLM model is unloaded (Ollama: `keep_alive: 0`) to free VRAM back for ComfyUI

This allows Ollama and ComfyUI to share a single GPU without running out of memory.

## API Endpoints

The node registers two HTTP endpoints for the JavaScript frontend:

- `GET /basify/llm_services` — returns configured service names
- `POST /basify/llm_models` — accepts `{"service": "name"}`, returns `{"models": [...]}`

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Empty output | Thinking model used all tokens on reasoning | Use a non-thinking model or increase `OLLAMA_NUM_CTX` |
| "Service unavailable" in dropdown | Service not running or unreachable | Start the service, check `base_url` |
| "Environment variable not set" | Missing API key | Set the env var (e.g., `export OPENAI_API_KEY=...`) |
| Parameter errors (temperature, top_p) | Reasoning model doesn't support sampling params | Handled automatically via retry |
| Model not persisted after restart | Old bug (fixed) | Model selection now persists in saved workflows |

## Class Reference

- **Class Name**: `LLMProcess`
- **Category**: `basify`
- **Display Name**: `Basify: LLM Process`
