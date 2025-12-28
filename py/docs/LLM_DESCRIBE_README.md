# Describe Image (LLM)

## Overview

The **Describe Image** node is a ComfyUI custom node that uses locally-running Ollama vision-language models to generate detailed natural language descriptions of images. It seamlessly integrates AI-powered image captioning into your ComfyUI workflows, with automatic model memory management and configurable generation parameters.

## Key Features

- **Local Processing**: Uses Ollama for privacy-friendly, offline image description
- **Vision Model Support**: Works with any Ollama vision-capable model (LLaVA, llama3.2-vision, etc.)
- **Automatic Memory Management**: Unloads models after use to free VRAM
- **Configurable Generation**: Adjustable temperature and token limits
- **Pass-through Design**: Returns both the original image and description
- **Batch Compatible**: Processes the first image from batches
- **Error Resilient**: Graceful error handling with informative messages
- **Colored Logging**: Console output with color-coded status messages

## Node Information

- **Node Name**: `BasifyDescribeImage`
- **Display Name**: `Describe Image`
- **Category**: `basify`
- **Output Node**: Yes (triggers execution)

## Prerequisites

### Ollama Installation

This node requires Ollama to be installed and running locally.

**Installation**:
- **Linux/macOS**: `curl https://ollama.ai/install.sh | sh`
- **Windows**: Download from [ollama.ai](https://ollama.ai)
- **Manual**: Visit [https://ollama.ai/download](https://ollama.ai/download)

**Verify Installation**:
```bash
ollama --version
```

### Vision Model Setup

Pull a vision-capable model:

```bash
# Recommended: LLaVA (fast, good quality)
ollama pull llava:latest

# Alternative: Llama 3.2 Vision (newer, larger)
ollama pull llama3.2-vision

# Smaller/faster option
ollama pull llava:7b

# More capable option
ollama pull llava:13b
```

**Start Ollama Server** (if not running):
```bash
ollama serve
```

The server runs on `http://localhost:11434` by default.

## Input Parameters

### Required Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image` | IMAGE | - | The image to describe (ComfyUI IMAGE tensor) |
| `model` | STRING | `"llava:latest"` | Ollama model name (must support vision) |
| `server_url` | STRING | `"http://localhost:11434/api/generate"` | Ollama API endpoint URL |

### Optional Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `temperature` | FLOAT | `0.7` | 0.0 - 2.0 | Controls randomness of outputs |
| `max_tokens` | INT | `500` | 10 - 4096 | Maximum tokens to generate |

## Output Values

| Output | Type | Description |
|--------|------|-------------|
| `image` | IMAGE | The original input image (pass-through) |
| `description` | STRING | Generated text description of the image |

## How It Works

### Processing Pipeline

1. **Input Processing**:
   - Receives ComfyUI IMAGE tensor (shape: `[B, H, W, C]`)
   - Extracts first image if batch provided
   - Converts from tensor to numpy array

2. **Format Conversion**:
   - Normalizes to 0-255 range if needed
   - Converts to PIL Image format
   - Encodes as JPEG in memory
   - Base64 encodes for API transmission

3. **API Request**:
   - Sends POST request to Ollama server
   - Includes base64 image and structured prompt
   - Applies temperature and token settings

4. **Response Parsing**:
   - Extracts description from JSON response
   - Strips whitespace and validates content
   - Handles empty or error responses

5. **Memory Cleanup**:
   - Attempts to unload model from VRAM
   - Uses `keep_alive: 0` to trigger immediate unload
   - Logs success/failure of cleanup

6. **Output**:
   - Returns original image unchanged
   - Returns description string for downstream use

### Prompt Engineering

The node uses a structured prompt:

```
DO describe the content of the image in detail. 
DO return only a single description of the image. 
DO return the description in a single sentence.

AVOID any additional text or explanations. 
AVOID returning anything other than a single description.
AVOID repeating the prompt or instructions in the response.
AVOID generating multiple descriptions or lists.
```

This ensures:
- Single, concise descriptions
- No meta-commentary
- Consistent output format
- No prompt repetition

### Model Memory Management

After generating a description, the node automatically unloads the model:

```python
unload_payload = {
    "model": model,
    "prompt": "",
    "keep_alive": 0  # Unload immediately
}
```

**Benefits**:
- Frees VRAM for other tasks
- Prevents model accumulation
- Allows multiple model usage in workflows
- Better resource efficiency

## Supported Models

### Recommended Models

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `llava:latest` | ~4.7GB | Fast | Good | General use, recommended |
| `llava:7b` | ~4.7GB | Fast | Good | Same as latest |
| `llava:13b` | ~8GB | Medium | Better | More detailed descriptions |
| `llama3.2-vision` | ~7.9GB | Medium | Excellent | Best quality, newer |
| `llama3.2-vision:11b` | ~7.9GB | Medium | Excellent | Alias for above |

### Model Requirements

**Must support**:
- Vision/multimodal capabilities
- Image input
- Ollama API format

**Will NOT work**:
- Text-only models (llama3, mistral, etc.)
- Models without vision encoders
- Non-Ollama models

## Usage Examples

### Basic Image Description

```
[Load Image] -> [Describe Image] -> description -> [Save Text]
                                 -> image -> [Save Image]
```

**Configuration**:
```
model: llava:latest
server_url: http://localhost:11434/api/generate
temperature: 0.7
max_tokens: 500
```

### Automated Captioning Pipeline

```
[Directory Auto Iterator] -> [Describe Image] -> [Save Image with Description]
```

Automatically generate captions for all images in a folder.

### Conditional Workflow Based on Content

```
[Load Image] -> [Describe Image] -> description -> [Parse Keywords]
                                                        |
                                                        v
                                            [Route Based on Content]
```

Use description to determine processing path.

### Multi-Model Comparison

```
[Load Image] -> [Describe Image (llava)] -> desc1 -> [Compare]
             -> [Describe Image (llama3.2)] -> desc2 ─┘
```

Compare descriptions from different models.

### Prompt Enhancement

```
[Load Image] -> [Describe Image] -> description -> [Combine with User Prompt]
                                                            |
                                                            v
                                                    [CLIP Text Encode]
```

Use AI-generated descriptions to enhance or replace manual prompts.

### Batch Processing with Logging

```
[Directory Iterator] -> [Describe Image] -> description -> [Append to File]
                                         -> image -> [Next Processing]
```

Build a dataset with images and captions.

## Parameter Tuning

### Temperature

Controls randomness and creativity in descriptions.

| Value | Behavior | Best For |
|-------|----------|----------|
| 0.0 - 0.3 | Deterministic, factual | Consistent captions, datasets |
| 0.4 - 0.7 | Balanced | General use |
| 0.8 - 1.2 | Creative, varied | Artistic descriptions |
| 1.3 - 2.0 | Highly varied | Experimental, multiple runs |

**Examples**:

**Temperature 0.2**:
> "A brown dog sitting on a wooden floor next to a blue toy."

**Temperature 0.7**:
> "A playful brown dog rests on hardwood flooring beside its favorite blue chew toy."

**Temperature 1.5**:
> "An adorable canine companion lounges contentedly on polished wooden planks, keeping watchful company over a well-loved azure plaything."

### Max Tokens

Controls description length.

| Value | Output Length | Best For |
|-------|---------------|----------|
| 50-100 | Very brief | Quick summaries, tags |
| 100-300 | Short sentence | Standard captions |
| 300-500 | Detailed sentence | Rich descriptions |
| 500-1000 | Paragraph | Comprehensive analysis |
| 1000+ | Multiple paragraphs | Detailed reports |

**Note**: Despite the prompt requesting single sentences, higher max_tokens allows more detail within that constraint.

## Server Configuration

### Custom Ollama Server

If running Ollama on a different machine or port:

```
server_url: http://192.168.1.100:11434/api/generate
```

### Docker/Container Setup

```bash
# Run Ollama in Docker
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Pull model inside container
docker exec -it ollama ollama pull llava:latest
```

**Node configuration**:
```
server_url: http://localhost:11434/api/generate
```

### Remote Server

```
server_url: https://your-ollama-server.com/api/generate
```

**Security Note**: Ensure HTTPS for remote servers to protect image data.

## Error Handling

### Common Errors

#### "Connection refused" / "Failed to connect"

**Causes**:
- Ollama server not running
- Wrong server URL
- Firewall blocking connection

**Solutions**:
```bash
# Start Ollama
ollama serve

# Check if running
curl http://localhost:11434/api/tags

# Verify server_url matches
```

#### "Model not found"

**Cause**: Model not pulled to Ollama

**Solution**:
```bash
# List available models
ollama list

# Pull missing model
ollama pull llava:latest
```

#### "No description generated"

**Causes**:
- Model doesn't support vision
- Image format issue
- API error

**Solutions**:
1. Verify model supports vision: `ollama show <model>`
2. Check ComfyUI console for detailed errors
3. Try a different model (e.g., `llava:latest`)
4. Test Ollama directly:
   ```bash
   ollama run llava:latest
   ```

#### "Error generating description: [details]"

**Cause**: API or processing error

**Solutions**:
1. Check console logs for full error
2. Verify image is valid
3. Test server_url in browser
4. Check Ollama logs: `ollama logs`

### Error Messages in Output

When errors occur, the description output contains:
```
"Error generating description: <error details>"
```

This allows workflows to continue while identifying failures.

## Console Logging

The node provides color-coded console output:

### Log Colors

| Color | Meaning | Example |
|-------|---------|---------|
| 🔵 Blue | Info/Status | `[BASIFY describe image] Processing image with model: llava:latest` |
| 🟢 Green | Success/Result | Description text |
| 🟡 Yellow | Warning | `Failed to unload model` |
| 🔴 Red | Error | `Error in image description: ...` |

### Log Messages

**Processing Start**:
```
[BASIFY describe image] Processing image with model: llava:latest
[BASIFY describe image] Sending request to Ollama server...
```

**Success**:
```
[BASIFY describe image] Successfully obtained image description:
[BASIFY describe image] A brown dog sitting on a wooden floor next to a blue toy.
```

**Model Unload**:
```
[BASIFY describe image] Unloading model: llava:latest from memory
[BASIFY describe image] Successfully unloaded model: llava:latest
```

**Warnings** (non-fatal):
```
[BASIFY describe image] Failed to unload model llava:latest: timeout
```

**Errors**:
```
[BASIFY] Error in image description: Connection refused
```

## Best Practices

### 1. Model Selection

**For Speed**:
- Use `llava:7b` (smallest vision model)
- Lower max_tokens (100-200)
- Higher temperature (0.8+) for varied short descriptions

**For Quality**:
- Use `llama3.2-vision` (best current option)
- Higher max_tokens (500-1000)
- Lower temperature (0.3-0.5) for consistency

**For Balance**:
- Use `llava:latest` (default)
- Default settings (temp=0.7, tokens=500)

### 2. Server Setup

- Run Ollama locally for best performance
- Use SSD storage for model files
- Allocate sufficient VRAM (4GB+ for most models)
- Keep Ollama updated: `ollama update`

### 3. Workflow Integration

**Passthrough Design**:
```
[Node A] -> image -> [Describe Image] -> image -> [Node B]
                                      -> description -> [Processing]
```

The passthrough design allows inserting description without disrupting image flow.

**Conditional Processing**:
```python
# In a custom node
if "person" in description.lower():
    # Apply portrait-specific processing
    pass
```

### 4. Performance Optimization

- Pre-pull models before workflows: `ollama pull llava:latest`
- Use smaller models for batch processing
- Consider disabling model unload for repeated use (requires Ollama modification)
- Process images at lower resolution before describing

### 5. Prompt Customization

For different description styles, modify the prompt in the source code:

**Detailed Technical**:
```python
prompt = "Describe this image in technical detail, including colors, composition, lighting, and objects."
```

**Artistic**:
```python
prompt = "Describe this image poetically, focusing on mood and atmosphere."
```

**Structured**:
```python
prompt = "Describe this image using this format: Subject, Setting, Action, Details."
```

## Troubleshooting

### Model Stays in Memory

**Problem**: Model not unloaded after use

**Cause**: Unload request failed or timeout

**Solution**:
- Check console for yellow warning
- Manually unload: `ollama stop <model>`
- Restart Ollama: `killall ollama && ollama serve`

### Slow Performance

**Problem**: Descriptions take too long

**Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| Large model | Use smaller model (llava:7b) |
| High max_tokens | Reduce to 200-300 |
| CPU mode | Ensure GPU support: `ollama run llava --gpu` |
| Large images | Resize before describing |
| Network latency | Use local server, not remote |

### Inconsistent Descriptions

**Problem**: Same image gives different descriptions

**Cause**: Temperature > 0 introduces randomness

**Solution**:
- Lower temperature to 0.0-0.3
- Run multiple times and average/select best
- Use deterministic model settings

### Empty Descriptions

**Problem**: Returns "No description generated"

**Debugging**:
```bash
# Test Ollama directly
ollama run llava:latest

# In Ollama prompt, describe an image
>>> Describe this: <paste base64 or use GUI>
```

**Check**:
- Model actually loaded
- API endpoint correct
- Response parsing working

### Memory Issues

**Problem**: Out of memory errors

**Solutions**:
- Use smaller model
- Close other applications
- Increase system swap
- Ensure GPU has sufficient VRAM

## Technical Details

### Image Processing

**Input Format**: ComfyUI IMAGE tensor
- Shape: `[batch, height, width, channels]`
- Channels: RGB (3)
- Values: 0.0-1.0 (float) or 0-255 (uint8)

**Conversion Steps**:
```python
1. Extract first image: image[0]
2. Convert to numpy: .cpu().numpy()
3. Normalize to 0-255: * 255 if needed
4. Convert to uint8: .astype(np.uint8)
5. Create PIL Image: Image.fromarray()
6. Save as JPEG: BytesIO buffer
7. Base64 encode: base64.b64encode()
```

**Why JPEG**?
- Smaller than PNG for transmission
- Lossy compression acceptable for description
- Wide compatibility
- Faster encoding

### API Communication

**Request Format** (Ollama API):
```json
{
  "model": "llava:latest",
  "prompt": "Describe this image...",
  "images": ["<base64-encoded-image>"],
  "stream": false,
  "temperature": 0.7,
  "options": {
    "num_predict": 500
  }
}
```

**Response Format**:
```json
{
  "model": "llava:latest",
  "created_at": "2025-12-28T...",
  "response": "A brown dog sitting on a wooden floor...",
  "done": true,
  "context": [...],
  "total_duration": 1234567890,
  "load_duration": 123456789,
  "prompt_eval_count": 10,
  "eval_count": 50
}
```

### Model Unloading

**Mechanism**:
```python
{
  "model": "llava:latest",
  "prompt": "",           # Empty prompt
  "keep_alive": 0         # Unload immediately
}
```

**Ollama Behavior**:
- `keep_alive > 0`: Keep in memory for N seconds
- `keep_alive = 0`: Unload immediately
- `keep_alive = -1`: Keep forever

## Integration Examples

### Caption to Filename

```
[Load Image] -> [Describe Image] -> description -> [Sanitize Text]
                                                        |
                                                        v
                              [Save Image with description as filename]
```

### Image Search Index

```
[Directory Iterator] -> [Describe Image] -> [Build Search Database]
                                                {filename: description}
```

Query later: "Find images with dogs" → Returns matching filenames.

### Content Moderation

```
[Input Image] -> [Describe Image] -> [Check for Keywords]
                                              |
                                              v
                                    [Allow/Block based on content]
```

### Automatic Tagging

```
[Image] -> [Describe Image] -> [Extract Nouns/Keywords] -> [Add Tags to Metadata]
```

### Multi-Language Workflow

```
[Image] -> [Describe Image (English)] -> [Translate to Target Language]
```

Or use multilingual models if available in Ollama.

## Performance Benchmarks

### Description Generation Time

| Model | Image Size | Speed (GPU) | Speed (CPU) |
|-------|------------|-------------|-------------|
| llava:7b | 512×512 | 2-4 sec | 15-30 sec |
| llava:7b | 1024×1024 | 3-6 sec | 20-40 sec |
| llava:13b | 512×512 | 4-8 sec | 30-60 sec |
| llama3.2-vision | 512×512 | 3-6 sec | 20-40 sec |

**Note**: Times vary based on hardware. RTX 3090 reference.

### Memory Usage

| Model | VRAM (GPU) | RAM (CPU) |
|-------|------------|-----------|
| llava:7b | ~4.5GB | ~8GB |
| llava:13b | ~7.5GB | ~14GB |
| llama3.2-vision:11b | ~7GB | ~12GB |

## Security Considerations

### Data Privacy

- **Local Processing**: Images never leave your machine (with local Ollama)
- **No Cloud**: Unlike commercial APIs, fully offline capable
- **No Telemetry**: Ollama doesn't send usage data

### Network Security

- Use `localhost` for local-only access
- Use HTTPS for remote servers
- Firewall Ollama port (11434) from internet
- Consider VPN for remote server access

### Model Trust

- Ollama models are from trusted sources
- Models downloaded from official Ollama registry
- Verify checksums if concerned: `ollama show <model> --modelfile`

## Compatibility

- **ComfyUI**: Any version with IMAGE tensor support
- **Python**: 3.8+
- **Ollama**: 0.1.0+
- **OS**: Windows, Linux, macOS (anywhere Ollama runs)
- **GPU**: NVIDIA (CUDA), AMD (ROCm), Apple Silicon (Metal)

## Comparison with Other Solutions

| Feature | Describe Image (Ollama) | BLIP/CLIP | Cloud APIs (GPT-4V) |
|---------|------------------------|-----------|---------------------|
| Privacy | ✅ Local | ✅ Local | ❌ Cloud |
| Cost | ✅ Free | ✅ Free | ❌ Per-request fee |
| Offline | ✅ Yes | ✅ Yes | ❌ Requires internet |
| Quality | 🟡 Good | 🟡 Basic | ✅ Excellent |
| Speed | 🟡 Medium | ✅ Fast | 🟡 Varies |
| Customization | ✅ Prompt control | ⚠️ Limited | ⚠️ API limits |
| Memory | 🟡 4-8GB | ✅ 1-2GB | ✅ None local |

## FAQ

**Q: Can I use this without Ollama?**
A: No, this node specifically uses the Ollama API. For other backends, modification would be needed.

**Q: Does this work with non-vision models?**
A: No, only vision-capable models like LLaVA and Llama 3.2 Vision work with images.

**Q: Can I customize the prompt?**
A: Yes, but requires modifying the source code. The prompt is hardcoded in the `describe_image` method.

**Q: Why does model unloading sometimes fail?**
A: Network timeouts or Ollama being busy. It's non-fatal; the model will auto-unload after Ollama's default timeout.

**Q: Can I process multiple images at once?**
A: The node processes only the first image from batches. For multiple images, use a loop or iterate through them.

**Q: How do I make descriptions more detailed?**
A: Increase `max_tokens` (500-1000) and use a larger model (`llama3.2-vision`).

**Q: Can I get descriptions in other languages?**
A: Modify the prompt to request specific languages. Results depend on model training.

**Q: Is there a rate limit?**
A: No API rate limits with local Ollama. Only limited by your hardware.

**Q: Can I run multiple describe nodes simultaneously?**
A: Yes, but they'll share VRAM. Ensure enough memory for concurrent models or they'll process sequentially.

**Q: How do I update models?**
A: `ollama pull <model>` downloads the latest version.
