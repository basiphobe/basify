# LLM Image Refine Node

## Overview

The **LLM Image Refine** node provides a two-stage AI processing pipeline for images:

1. **Stage 1 (Vision)**: A vision-capable model (e.g., LLaVA) analyzes the image and generates a description
2. **Stage 2 (Text Processing)**: A text model processes the description according to user-provided instructions

This allows you to not only describe images but also transform, enhance, or manipulate those descriptions in creative ways.

## Inputs

### Required

- **image** (`IMAGE`): The input image to process
- **vision_model** (`STRING`): Ollama model with vision capabilities (e.g., `llava:latest`, `llava:13b`, `bakllava`)
- **text_model** (`STRING`): Ollama text model for processing the description (e.g., `llama3.2:latest`, `mistral`, `mixtral`)
- **user_instructions** (`STRING`, multiline): Instructions for how to process the image description

### Optional

- **custom_vision_prompt** (`STRING`, multiline): Custom system prompt for the vision stage (overrides default)
- **vision_temperature** (`FLOAT`, 0.0-2.0, default: 0.3): Randomness for vision model
- **vision_top_p** (`FLOAT`, 0.0-1.0, default: 0.95): Nucleus sampling for vision model
- **vision_top_k** (`INT`, 1-100, default: 40): Top-k sampling for vision model
- **text_temperature** (`FLOAT`, 0.0-2.0, default: 0.7): Randomness for text model
- **text_presence_penalty** (`FLOAT`, -2.0-2.0, default: 0.0): Penalize repeated topics
- **text_frequency_penalty** (`FLOAT`, -2.0-2.0, default: 0.0): Penalize repeated tokens
- **text_top_p** (`FLOAT`, 0.0-1.0, default: 0.95): Nucleus sampling for text model
- **text_top_k** (`INT`, 1-100, default: 40): Top-k sampling for text model

## Outputs

1. **image** (`IMAGE`): Passthrough of the input image
2. **description** (`STRING`): Raw description from the vision model
3. **refined_output** (`STRING`): Processed/refined description from the text model

## Use Cases

### 1. **Enhanced Descriptions**
```
Vision Model: llava:latest
Text Model: llama3.2:latest
Instructions: "Expand this description to include more sensory details, emotions, and atmospheric elements. Make it more vivid and immersive."
```

### 2. **Creative Reinterpretation**
```
Vision Model: llava:13b
Text Model: mixtral:latest
Instructions: "Rewrite this description as if it were a scene from a fantasy novel. Add magical elements and epic language."
```

### 3. **Technical Analysis**
```
Vision Model: llava:latest
Text Model: mistral:latest
Instructions: "Convert this description into a technical specification listing all visible components, colors (with hex codes if possible), and spatial relationships."
```

### 4. **Style Transfer**
```
Vision Model: bakllava
Text Model: llama3.2
Instructions: "Transform this description into the style of a 1920s newspaper article."
```

### 5. **Keyword Extraction**
```
Vision Model: llava:latest
Text Model: llama3.2
Instructions: "Extract only the key nouns, adjectives, and important concepts from this description. Return as a comma-separated list suitable for image generation prompts."
```

### 6. **Translation + Enhancement**
```
Vision Model: llava:latest
Text Model: llama3.2
Instructions: "Translate this to Spanish and enhance it with poetic language."
```

## Workflow Integration

### Basic Workflow
```
[Load Image] → [LLM Image Refine] → [Display Anything] (to view outputs)
                                   → [Save Image] (using refined_output as filename metadata)
```

### Advanced Workflow
```
[Load Image] → [LLM Image Refine] → [Wildcard Processor] → [Text to Image]
                                                          → [Save Image]
```

This allows you to:
1. Describe an image with AI
2. Refine/enhance the description
3. Use that refined description as a prompt for new image generation

## Technical Details

### Memory Management

The node implements aggressive cleanup following Basify conventions:
- Unloads ComfyUI models before Ollama processing
- Forces cache cleanup between stages
- Explicitly deletes large objects in `finally` blocks
- Unloads Ollama models after each stage

### Processing Flow

```
1. Image Input (tensor)
2. Force ComfyUI model unload
3. STAGE 1: Vision model processes image → description
4. Model unload + cache cleanup
5. STAGE 2: Text model processes description + instructions → refined output
6. Model unload + cleanup
7. Return (image, description, refined_output)
```

### Error Handling

- If vision stage fails, returns error message in both description and refined_output
- If text stage fails, returns original description and error message in refined_output
- Always returns the original image for passthrough

## Tips

### Model Selection

**Vision Models (Stage 1)**:
- `llava:latest` - Fast, good quality, 7B parameters
- `llava:13b` - Higher quality, slower, 13B parameters
- `bakllava` - Alternative architecture, good for detailed descriptions

**Text Models (Stage 2)**:
- `llama3.2:latest` - Balanced, good instruction following
- `mistral:latest` - Fast, concise outputs
- `mixtral:latest` - High quality, creative, larger model

### Temperature Settings

**Vision Stage** (default 0.3):
- Lower (0.1-0.3) for factual, consistent descriptions
- Higher (0.7-1.0) for more creative interpretations

**Text Stage** (default 0.7):
- Lower (0.3-0.5) for precise transformations
- Higher (0.7-1.2) for creative rewriting

### Performance

- Each stage requires loading a model into VRAM
- Using the same model for both stages can reduce total processing time
- Vision models are typically larger and slower than text-only models
- Consider using smaller models (7B) for faster iteration

## Examples

### Example 1: Comic Book Description
```
Instructions: "Rewrite this as a comic book panel description. Include suggested camera angles, dramatic lighting notes, and character expressions."

Input Image: Photo of a person reading
Output: "WIDE SHOT - Late afternoon sunlight streams through venetian blinds (HIGH CONTRAST shadows). PROTAGONIST sits in worn leather armchair, knees drawn up, paperback held close. Their eyes are wide with surprise, eyebrows raised. Suggested angle: LOW, looking up at character to emphasize their absorption in the story..."
```

### Example 2: SEO-Optimized Description
```
Instructions: "Convert this into an SEO-optimized alt text description. Include relevant keywords while maintaining natural language. Maximum 125 characters."

Input Image: Product photo
Output: "Stainless steel coffee maker with glass carafe on marble countertop - modern kitchen appliance for brewing"
```

## Troubleshooting

### "Error: Empty response from model"
- Ensure Ollama is running (`ollama serve`)
- Verify the selected models are installed (`ollama list`)
- Check model supports vision (for vision_model)

### High VRAM usage
- Use smaller models (7B instead of 13B)
- Ensure models are being unloaded (check logs)
- Reduce batch size if processing multiple images

### Slow processing
- Consider using the same model for both stages
- Use smaller/faster models like `mistral` or `llama3.2`
- Increase temperature slightly to reduce token generation time

## Related Nodes

- **Ollama Process**: Single-stage text processing
- **LLM Describe**: Simple image description (single stage only)
- **Wildcard Processor**: Process refined output for prompt generation
- **Display Anything**: View intermediate outputs

## Model Requirements

- **Ollama installed and running**: `http://localhost:11434` (configurable via `OLLAMA_BASE_URL` env var)
- **Vision model installed**: At least one model with vision capabilities (e.g., `ollama pull llava`)
- **Text model installed**: Any text-generation model (e.g., `ollama pull llama3.2`)
