# Ollama Text Processing - Documentation

A ComfyUI node for processing text through locally-hosted Ollama models with full control over generation parameters.

## Features

- **Local Model Inference** - Process text using Ollama models running on your machine
- **Model Selection** - Automatic discovery and selection of available Ollama models
- **Configurable Parameters** - Fine-tune temperature, top_p, and top_k for generation control
- **System Prompts** - Define AI behavior with custom system instructions
- **Memory Management** - Automatic model loading/unloading to optimize VRAM usage
- **Error Handling** - Graceful error handling with detailed logging

---

## Prerequisites

### 1. Install Ollama

Download and install Ollama from [ollama.ai](https://ollama.ai)

### 2. Pull Models

Pull at least one model before using the node:

```bash
# Example: Pull the Llama 3.2 model
ollama pull llama3.2

# Or pull other models
ollama pull mistral
ollama pull phi3
ollama pull qwen2.5
```

### 3. Install Python Package

The `ollama` Python package is required:

```bash
pip install ollama
```

### 4. Start Ollama Server

Ensure the Ollama server is running (usually starts automatically on installation):

```bash
ollama serve
```

---

## Input Parameters

### Required Inputs

#### `text` (STRING)
The input text to process through the Ollama model.

**Multiline:** Yes  
**Placeholder:** "Enter text to process..."

**Examples:**
```
Summarize the following article in 3 bullet points: ...

Translate this to Spanish: Hello, how are you?

Write a short poem about winter.
```

#### `model` (DROPDOWN)
Select from available Ollama models installed on your system.

**Auto-detected:** Yes  
**Default:** First available model

The dropdown automatically populates with all models found via `ollama list`.

**Common Models:**
- `llama3.2` - Meta's Llama 3.2 (various sizes)
- `mistral` - Mistral AI's models
- `phi3` - Microsoft's Phi-3 models
- `qwen2.5` - Alibaba's Qwen 2.5 models
- `gemma2` - Google's Gemma 2 models

#### `system_prompt` (STRING)
System-level instructions that define the AI's behavior and response style.

**Multiline:** Yes  
**Default:** "You are a helpful assistant. Provide clear, accurate, and helpful responses to user queries."

**Examples:**

```
You are a creative writing assistant specializing in science fiction. 
Use vivid imagery and maintain a sense of wonder in your responses.
```

```
You are a professional code reviewer. Analyze code for bugs, 
performance issues, and best practices. Be concise and specific.
```

```
You are a patient teacher explaining concepts to a beginner. 
Use simple language, analogies, and step-by-step explanations.
```

#### `temperature` (FLOAT)
Controls randomness in the model's output.

**Range:** 0.0 - 2.0  
**Default:** 0.3  
**Step:** 0.05

- **0.0** - Deterministic, always picks the most likely token (repetitive)
- **0.3** - Low creativity, focused and consistent (recommended for factual tasks)
- **0.7** - Balanced creativity and coherence (general purpose)
- **1.0** - High creativity, more varied responses
- **1.5+** - Very creative, potentially less coherent

**Use Cases:**
- **0.1-0.3** - Code generation, factual summaries, translations
- **0.5-0.8** - Creative writing, brainstorming, conversational AI
- **1.0-2.0** - Experimental creative generation, poetry

#### `top_p` (FLOAT)
Nucleus sampling: considers tokens whose cumulative probability reaches this threshold.

**Range:** 0.0 - 1.0  
**Default:** 0.95  
**Step:** 0.01

- **0.1** - Very narrow selection (only most likely tokens)
- **0.5** - Moderate selection
- **0.95** - Wide selection (recommended default)
- **1.0** - All tokens considered

**Interaction with Temperature:**
- Use `top_p` for controlling diversity
- Use `temperature` for controlling randomness
- For most use cases, `top_p=0.95` works well

#### `top_k` (INT)
Limits selection to the top K most likely tokens.

**Range:** 1 - 100  
**Default:** 40  
**Step:** 1

- **1** - Always pick the most likely token (deterministic)
- **10-20** - Conservative selection
- **40** - Balanced (recommended default)
- **80-100** - Wide selection, more diverse outputs

**When to Adjust:**
- Lower for more focused, predictable output
- Higher for more creative, varied output
- Often used in combination with `temperature` and `top_p`

---

## Output

### `STRING`
The processed text response from the Ollama model.

Returns the complete model response as a string that can be:
- Displayed in the UI
- Saved to file using the Save Image node's text export feature
- Passed to other nodes for further processing
- Used as input for subsequent prompts

---

## Usage Examples

### Example 1: Text Summarization

```yaml
text: "Long article text here..."
model: llama3.2
system_prompt: "You are a summarization expert. Create concise summaries that capture key points."
temperature: 0.3
top_p: 0.95
top_k: 40
```

### Example 2: Creative Writing

```yaml
text: "Write a short story about a time-traveling detective."
model: mistral
system_prompt: "You are a creative fiction writer specializing in sci-fi noir."
temperature: 0.9
top_p: 0.95
top_k: 60
```

### Example 3: Code Review

```yaml
text: "def calculate(x, y):\n    return x + y"
model: phi3
system_prompt: "You are a Python expert. Review code for bugs, style, and best practices."
temperature: 0.2
top_p: 0.9
top_k: 30
```

### Example 4: Translation

```yaml
text: "Hello, how are you today?"
model: qwen2.5
system_prompt: "You are a professional translator. Translate text to Spanish naturally."
temperature: 0.2
top_p: 0.95
top_k: 40
```

---

## Workflow Integration

### Example: Image Description Pipeline

```
LoadImage → [image] → LLM Describe → [description] 
                                              ↓
                                    Ollama Process → [enhanced description]
                                              ↓
                                        Save Image (with text export)
```

**Configuration:**
- **LLM Describe:** Generate initial image description
- **Ollama Process:** 
  - text: `{description from LLM Describe}`
  - system_prompt: "Enhance this image description with vivid details and artistic language"
  - temperature: 0.7

### Example: Iterative Text Refinement

```
String Input → Ollama Process #1 → Ollama Process #2 → Final Output
```

**Configuration:**
- **Ollama #1:** Draft generation (temperature: 0.8)
- **Ollama #2:** Refinement and polishing (temperature: 0.3)

---

## Performance Considerations

### Memory Management

The node automatically manages model memory:

1. **Pre-processing:** Unloads all ComfyUI models and clears cache
2. **Processing:** Loads the selected Ollama model
3. **Post-processing:** Unloads the Ollama model to free VRAM

This prevents VRAM conflicts between image generation models and LLM models.

### Model Size vs. Speed

| Model Size | VRAM Usage | Speed | Quality |
|------------|------------|-------|---------|
| 1B-3B (e.g., phi3-mini) | 2-4 GB | Fast | Good for simple tasks |
| 7B (e.g., llama3.2:7b) | 4-8 GB | Medium | Balanced |
| 13B+ (e.g., llama3.2:13b) | 8-16+ GB | Slow | Best quality |

**Recommendations:**
- **Low VRAM (8GB):** Use 3B or smaller models
- **Medium VRAM (16GB):** Use 7B models
- **High VRAM (24GB+):** Use 13B+ models

### Optimization Tips

1. **Model Selection:**
   - Use quantized models (Q4, Q5) for faster inference
   - Example: `llama3.2:7b-q4_0` vs `llama3.2:7b`

2. **Parameter Tuning:**
   - Lower `top_k` for faster inference
   - Use lower `temperature` when deterministic output is acceptable

3. **Batch Processing:**
   - Process multiple texts in sequence
   - Models stay loaded between same-model requests

---

## Troubleshooting

### "No models found!"

**Cause:** No Ollama models are installed  
**Solution:**
```bash
ollama pull llama3.2
# Restart ComfyUI to refresh the model list
```

### Connection Errors

**Cause:** Ollama server not running  
**Solution:**
```bash
ollama serve
# Or check if running: curl http://localhost:11434
```

**Cause:** Custom Ollama port/host  
**Solution:** The node uses the default Ollama host (http://localhost:11434). If using a custom configuration, you may need to set the `OLLAMA_HOST` environment variable:
```bash
export OLLAMA_HOST=http://your-host:port
```

### "ImportError: ollama package is not installed"

**Solution:**
```bash
pip install ollama
# Restart ComfyUI
```

### Slow Performance

**Solutions:**
1. Use a smaller/quantized model
2. Reduce `top_k` value
3. Ensure no other applications are using VRAM
4. Check that CUDA/ROCm drivers are properly installed

### Model Loading Errors

**Cause:** Insufficient VRAM  
**Solution:**
- Use a smaller model
- Close other applications
- Enable model offloading in Ollama:
  ```bash
  # Set environment variable for CPU offloading
  export OLLAMA_NUM_GPU=0  # Use CPU only
  export OLLAMA_NUM_GPU=1  # Limit to 1 GPU layer
  ```

---

## Advanced Configuration

### Environment Variables

Set these before starting ComfyUI:

```bash
# Custom Ollama host
export OLLAMA_HOST=http://localhost:11434

# Limit GPU memory usage (in MB)
export OLLAMA_MAX_VRAM=8192

# Number of GPU layers to offload
export OLLAMA_NUM_GPU=35
```

### System Prompt Best Practices

**Be Specific:**
```
❌ "You are helpful."
✅ "You are a technical writer creating documentation for developers. Use clear, concise language with code examples."
```

**Define Constraints:**
```
You are a content editor. Keep responses under 100 words. 
Use simple language suitable for 8th-grade reading level.
```

**Set Response Format:**
```
You are a data analyst. Respond in this format:
1. Key Finding
2. Supporting Data
3. Recommendation
```

---

## Model Recommendations

### General Purpose
- **llama3.2:latest** - Excellent balance of quality and speed
- **mistral:latest** - Fast, efficient for most tasks

### Coding
- **phi3:latest** - Microsoft's code-focused model
- **codellama:latest** - Specialized for programming

### Creative Writing
- **mistral:latest** - Good storytelling capabilities
- **llama3.2:13b** - Higher quality, more creative (if VRAM permits)

### Multilingual
- **qwen2.5:latest** - Strong multilingual support
- **gemma2:latest** - Good for translation tasks

---

## API Reference

### Node Class

**Class Name:** `OllamaProcess`  
**Display Name:** "Ollama Text Processing"  
**Category:** "basify"

### Methods

#### `process_text(text, model, system_prompt, temperature, top_p, top_k)`

Processes input text through the selected Ollama model.

**Parameters:**
- `text` (str): Input text to process
- `model` (str): Model name from dropdown
- `system_prompt` (str): System instructions
- `temperature` (float): Randomness control (0.0-2.0)
- `top_p` (float): Nucleus sampling threshold (0.0-1.0)
- `top_k` (int): Top-K sampling limit (1-100)

**Returns:**
- `tuple[str]`: Single-element tuple containing the model's response

**Raises:**
- Returns error message string if processing fails

---

## Logging

The node provides detailed console logging with color coding:

- **🔵 BLUE:** General information
- **🟡 YELLOW:** Warnings and processing updates
- **🟢 GREEN:** Success messages
- **🔴 RED:** Errors

**Example Output:**
```
[BASIFY OllamaNode] Processing text with model: llama3.2
[BASIFY OllamaNode] Processing with model: llama3.2
[BASIFY OllamaNode] Text processed successfully
```

---

## License

Part of the Basify custom node collection for ComfyUI.

---

## Support

For issues, questions, or feature requests, please visit the [Basify GitHub repository](https://github.com/basiphobe/basify).
