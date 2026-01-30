# Latent Upscaler Node

## Overview
The **Latent Upscaler** node provides functionality to upscale latent tensors using upscale models in ComfyUI workflows. This node allows you to increase the resolution of latent representations before decoding to pixel space, which can improve final image quality.

## Features
- **Upscale Model Support**: Works with any upscale model loaded via ComfyUI's core upscale model loader
- **Flexible Scaling**: Configurable upscale factor from 1.0x to 8.0x
- **Memory Efficient**: Implements aggressive cleanup to prevent VRAM leaks
- **Standard Format**: Uses ComfyUI's standard latent tensor format

## Inputs

### Required
- **upscale_model** (`UPSCALE_MODEL`): Upscale model from the core upscale model loader
  - Load this using ComfyUI's "Load Upscale Model" node
  - Examples: RealESRGAN, ESRGAN, SwinIR, etc.

- **latent** (`LATENT`): Input latent tensor to upscale
  - Standard ComfyUI latent format (from VAE Encode, KSampler, etc.)

- **upscale_by** (`FLOAT`): Upscale factor
  - Range: 1.0 to 8.0
  - Default: 2.0
  - Step: 0.1
  - Examples:
    - `1.5` = 50% larger
    - `2.0` = 2x size (double width and height)
    - `4.0` = 4x size (quadruple dimensions)

## Outputs
- **upscaled_latent** (`LATENT`): The upscaled latent tensor
  - Maintains the same format as input latent
  - Dimensions scaled by the specified factor
  - Can be passed to KSampler, VAE Decode, or other latent-accepting nodes

## Usage Examples

### Basic Upscaling Workflow
```
Load Upscale Model → upscale_model
                                    ↓
VAE Encode → latent → Latent Upscaler → upscaled_latent → KSampler → VAE Decode
                                    ↑
                      upscale_by: 2.0
```

### Multi-Stage Upscaling
```
KSampler → latent → Latent Upscaler (2x) → KSampler → Latent Upscaler (1.5x) → VAE Decode
```

### Combined with Latent Generator
```
Latent Generator → Latent Upscaler (1.5x) → KSampler → VAE Decode
```

## Technical Details

### Latent Space Upscaling
- Uses bicubic interpolation for smooth upscaling
- Operates directly on latent tensors (not pixel data)
- Latent format: `[batch_size, channels, height, width]`
- Upscales the height and width dimensions by the specified factor

### Memory Management
The node implements ComfyUI best practices for memory management:
- Explicit tensor cleanup in `finally` block
- Garbage collection after processing
- CUDA cache clearing when GPU is available
- Prevents memory leaks in long-running ComfyUI sessions

### Performance Considerations
- Larger upscale factors require more VRAM
- 2x upscale = 4x memory usage (area increases quadratically)
- Consider system capabilities when using high upscale factors

## Tips and Best Practices

1. **Upscale Factor Selection**:
   - For most cases, 2x (2.0) is a good balance
   - Higher factors (4x+) may require significant VRAM
   - Use incremental upscaling (2x → 1.5x) instead of single large upscale for better results

2. **Workflow Integration**:
   - Upscale latents before final sampling for higher resolution outputs
   - Combine with KSampler for iterative refinement at higher resolutions
   - Chain multiple upscalers for extreme resolution increases

3. **Model Selection**:
   - Different upscale models may have varying effects
   - Experiment with different models for best results
   - Some models are optimized for specific content types (faces, textures, etc.)

4. **Memory Management**:
   - Monitor VRAM usage when using high upscale factors
   - Clear unused models from memory before upscaling
   - Use batch size 1 for very large upscales

## Common Issues

### Out of Memory Errors
- **Solution**: Reduce upscale factor or use multi-stage upscaling
- **Example**: Instead of 4x, use 2x → 2x in separate steps

### Artifacts in Output
- **Cause**: May occur with very high upscale factors
- **Solution**: Use incremental upscaling or try different upscale models

## Version History
- **v1.0.0**: Initial release with bicubic interpolation upscaling

## Related Nodes
- **Latent Generator**: Generate latents at specific resolutions
- **Load Upscale Model**: Load upscale models for use with this node
- **KSampler**: Sample latents at upscaled resolutions
- **VAE Decode**: Convert upscaled latents to images
