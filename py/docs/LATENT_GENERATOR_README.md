# Latent Generator

## Overview

The **Latent Generator** is a ComfyUI custom node that creates empty latent tensors for image generation workflows. It offers flexible resolution selection through either predefined aspect ratios or manual dimension input, making it easy to generate images at common sizes without manual calculation.

## Key Features

- **Dual Mode Operation**: Switch between predefined resolutions and manual dimensions
- **Comprehensive Presets**: 25+ predefined resolutions covering common aspect ratios
- **Aspect Ratio Organization**: Resolutions grouped by aspect ratio (1:1, 16:9, 3:4, etc.)
- **Batch Support**: Generate multiple latents in a single batch
- **Automatic Validation**: Ensures dimensions are valid for latent space (multiples of 8)
- **Standard Output**: Compatible with all ComfyUI samplers and latent processors

## Node Information

- **Node Name**: `BasifyLatentGenerator`
- **Display Name**: `Basify: Latent Generator`
- **Category**: `latent`

## Input Parameters

### Required Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resolution_mode` | DROPDOWN | `"predefined"` | Choose between predefined resolutions or manual input (`predefined`/`manual`) |
| `predefined_resolution` | DROPDOWN | `"768×1024 (3:4) - Portrait"` | Select from preset resolutions (active when mode is `predefined`) |
| `manual_width` | INT | `512` | Custom width in pixels (active when mode is `manual`) |
| `manual_height` | INT | `768` | Custom height in pixels (active when mode is `manual`) |
| `batch_size` | INT | `1` | Number of latent tensors to generate |

#### Manual Dimension Constraints
- **Min**: 16 pixels
- **Max**: 16384 pixels
- **Step**: 8 pixels
- **Requirement**: Must be multiples of 8

#### Batch Size Constraints
- **Min**: 1
- **Max**: 4096

## Output Values

| Output | Type | Description |
|--------|------|-------------|
| `latent` | LATENT | Empty latent tensor in ComfyUI format |
| `width` | INT | Width in pixels (useful for downstream nodes) |
| `height` | INT | Height in pixels (useful for downstream nodes) |

## Predefined Resolutions

### Square (1:1)
Perfect for general-purpose images and social media posts.

| Resolution | Description | Aspect Ratio |
|------------|-------------|--------------|
| 512×512 | Small square | 1:1 |
| 768×768 | Standard square | 1:1 |
| 832×832 | Medium square | 1:1 |
| 1024×1024 | Large square | 1:1 |

### Portrait (3:4)
Classic portrait orientation, ideal for character art and portraits.

| Resolution | Description | Aspect Ratio |
|------------|-------------|--------------|
| 576×768 | Small portrait | 3:4 |
| 672×896 | Medium portrait | 3:4 |
| 768×1024 | Portrait | 3:4 |

### Landscape (4:3)
Classic landscape orientation, ideal for scenery and wide shots.

| Resolution | Description | Aspect Ratio |
|------------|-------------|--------------|
| 768×576 | Small landscape | 4:3 |
| 896×672 | Medium landscape | 4:3 |
| 1024×768 | Landscape | 4:3 |

### Widescreen (16:9)
Cinematic and video format, great for wallpapers and panoramic views.

| Resolution | Description | Aspect Ratio |
|------------|-------------|--------------|
| 896×512 | Small widescreen | 16:9 |
| 1152×648 | Medium widescreen | 16:9 |
| 1344×768 | Widescreen | 16:9 |
| 1536×864 | Widescreen large | 16:9 |

### Vertical Video (9:16)
Mobile and social media format (Instagram Stories, TikTok, etc.).

| Resolution | Description | Aspect Ratio |
|------------|-------------|--------------|
| 512×896 | Small vertical | 9:16 |
| 648×1152 | Medium vertical | 9:16 |
| 768×1344 | Vertical | 9:16 |
| 864×1536 | Vertical large | 9:16 |

### Photo Portrait (2:3)
Standard photographic portrait format.

| Resolution | Description | Aspect Ratio |
|------------|-------------|--------------|
| 576×832 | Small photo portrait | 2:3 |
| 704×1024 | Medium photo portrait | 2:3 |
| 832×1216 | Photo portrait | 2:3 |

### Photo Landscape (3:2)
Standard photographic landscape format.

| Resolution | Description | Aspect Ratio |
|------------|-------------|--------------|
| 832×576 | Small photo landscape | 3:2 |
| 1024×704 | Medium photo landscape | 3:2 |
| 1216×832 | Photo landscape | 3:2 |

### Golden Ratio (5:8 / 8:5)
Aesthetically pleasing proportions based on the golden ratio.

| Resolution | Description | Aspect Ratio |
|------------|-------------|--------------|
| 832×1280 | Golden portrait | 5:8 |
| 1280×832 | Golden landscape | 8:5 |

## How It Works

### Latent Space Basics

In Stable Diffusion and similar models:
- Images are processed in **latent space** (compressed representation)
- Latent dimensions are **1/8th** of pixel dimensions
- Each latent has **4 channels** (learned representation)
- Pixel dimensions must be **multiples of 8** for proper encoding/decoding

### Tensor Generation

The node creates a zero-initialized tensor with shape:
```
[batch_size, 4, height÷8, width÷8]
```

**Example**: For 768×1024 resolution with batch_size=1:
```python
latent_shape = [1, 4, 128, 96]  # 1024÷8=128, 768÷8=96
```

### Device Management

The node uses ComfyUI's `intermediate_device()` for optimal memory management:
- Automatically selects appropriate device (CPU/GPU)
- Follows ComfyUI's memory management strategy
- Ensures compatibility with the rest of the workflow

## Usage Examples

### Basic Image Generation

**Predefined Mode**:
1. Add **Basify: Latent Generator** to your workflow
2. Keep `resolution_mode` as `"predefined"`
3. Select desired resolution (e.g., `"768×1024 (3:4) - Portrait"`)
4. Connect `latent` output to a KSampler
5. Generate your image

**Manual Mode**:
1. Change `resolution_mode` to `"manual"`
2. Set `manual_width` (e.g., 512)
3. Set `manual_height` (e.g., 768)
4. Connect `latent` output to a KSampler

### Batch Generation

Generate multiple variations at once:
```
resolution_mode: predefined
predefined_resolution: "1024×1024 (1:1) - Large square"
batch_size: 4
```

This creates 4 latent tensors, allowing the sampler to generate 4 different images in one pass.

### Using Dimension Outputs

The `width` and `height` outputs can be used for:
- **Conditional scaling**: Pass to upscale nodes
- **Metadata tracking**: Save generation dimensions
- **Dynamic workflows**: Adjust processing based on image size

Example workflow:
```
[Latent Generator] -> latent -> [KSampler] -> [VAE Decode] -> [Save Image]
                   -> width ──┐
                   -> height ─┴─> [Image Upscaler with dynamic target size]
```

### Social Media Optimized Generations

**Instagram Post** (1:1):
```
predefined_resolution: "1024×1024 (1:1) - Large square"
```

**Instagram Story** (9:16):
```
predefined_resolution: "768×1344 (9:16) - Vertical"
```

**YouTube Thumbnail** (16:9):
```
predefined_resolution: "1344×768 (16:9) - Widescreen"
```

**Twitter/X Header** (3:1 - use manual):
```
resolution_mode: manual
manual_width: 1500
manual_height: 500
```

## Validation and Error Handling

### Automatic Validation

The `VALIDATE_INPUTS` method checks:
- **Manual width**: Must be multiple of 8
- **Manual height**: Must be multiple of 8

**Invalid Examples**:
- ❌ Width: 513 (not divisible by 8)
- ❌ Height: 770 (not divisible by 8)

**Valid Examples**:
- ✅ Width: 512 (512 ÷ 8 = 64)
- ✅ Height: 768 (768 ÷ 8 = 96)

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `"Manual width must be a multiple of 8, got X"` | Width not divisible by 8 | Adjust width to nearest multiple of 8 |
| `"Manual height must be a multiple of 8, got X"` | Height not divisible by 8 | Adjust height to nearest multiple of 8 |
| `"Failed to parse predefined resolution..."` | Corrupted preset string | Report as bug / use manual mode |

## Best Practices

### 1. Choosing Resolution Mode

**Use Predefined When**:
- Working with standard aspect ratios
- Need quick setup without calculations
- Creating content for specific platforms
- Want consistent, tested dimensions

**Use Manual When**:
- Need exact custom dimensions
- Working with non-standard aspect ratios
- Matching specific input image sizes
- Experimental or specialized workflows

### 2. Resolution Selection Guidelines

**For Speed** (faster generation):
- Use smaller resolutions (512×512, 576×768)
- Lower batch sizes
- Square or smaller aspect ratios

**For Quality** (better details):
- Use larger resolutions (1024×1024, 1344×768)
- Single or small batch sizes
- Consider VRAM limitations

**For VRAM Efficiency**:
| VRAM | Recommended Max Resolution | Max Batch |
|------|---------------------------|-----------|
| 4GB | 512×512 | 1-2 |
| 6GB | 768×768 | 1-4 |
| 8GB | 1024×1024 | 1-4 |
| 12GB+ | 1536×864 | 4+ |

### 3. Batch Size Optimization

**Small Batches (1-4)**:
- Interactive workflows
- High-resolution images
- Limited VRAM
- Testing and experimentation

**Medium Batches (5-16)**:
- Variation generation
- A/B testing prompts
- Style exploration
- Grid comparisons

**Large Batches (17+)**:
- Mass production
- Dataset generation
- Abundant VRAM
- Automated workflows

### 4. Aspect Ratio Selection

**1:1 (Square)**:
- Profile pictures
- Icons and logos
- General-purpose content
- Most flexible for cropping

**16:9 (Widescreen)**:
- Desktop wallpapers
- Video thumbnails
- Cinematic compositions
- Landscape photography

**9:16 (Vertical)**:
- Mobile wallpapers
- Social media stories
- Portrait photography
- Smartphone content

**3:4 / 4:3 (Traditional)**:
- Classic portrait/landscape
- Print photography
- Artistic compositions
- Gallery displays

### 5. Memory Management

- Larger dimensions = more VRAM usage
- Batch size multiplies VRAM requirements
- Monitor VRAM usage in ComfyUI console
- Use lower resolutions if encountering OOM errors

## Integration Examples

### Basic Txt2Img Workflow
```
[Latent Generator] -> [KSampler] -> [VAE Decode] -> [Save Image]
                        ↑   ↑
                [CLIP Encode] [Model Loader]
```

### Batch Variation Generator
```
[Latent Generator (batch=4)] -> [KSampler] -> [VAE Decode] -> [Save Image]
                                    ↑
                            [Randomize Seed per Batch]
```

### Multi-Resolution Output
```
[Latent Generator (512×512)]  ──┐
[Latent Generator (1024×1024)]  ├─> [Switch] -> [KSampler] -> ...
[Latent Generator (1344×768)]  ─┘
```

### Dynamic Size Workflow
```
[Latent Generator] -> width  ──┐
                   -> height ──┼─> [Math Node] -> [Calculate upscale factor]
                   -> latent ──┘
```

## Technical Details

### Tensor Format

**Shape**: `[batch_size, channels, latent_height, latent_width]`

**Components**:
- `batch_size`: Number of images to generate
- `channels`: Always 4 (standard latent channels)
- `latent_height`: `pixel_height ÷ 8`
- `latent_width`: `pixel_width ÷ 8`

**Data Type**: `torch.float32` (or device default)
**Initialization**: Zeros (neutral starting point for diffusion)

### Why Zeros?

Empty latents are initialized with zeros because:
- Diffusion models start from noise (added by sampler)
- Zero is a neutral starting point
- Allows sampler to add controlled noise
- Compatible with all sampling algorithms

### Device Selection

```python
device = comfy.model_management.intermediate_device()
```

This selects:
- **GPU**: If available and has sufficient VRAM
- **CPU**: If GPU is full or unavailable
- **MPS**: On Apple Silicon Macs with MPS support

### Predefined Resolution Parsing

Format: `"WIDTH×HEIGHT (RATIO) - Description"`

Example: `"768×1024 (3:4) - Portrait"`
- Extracts: `768×1024`
- Splits on: `×`
- Converts to: `width=768, height=1024`

### Multiple of 8 Requirement

**Why Required**?
- VAE encoder/decoder uses 8× downsampling/upsampling
- Latent space is 1/8th the pixel dimensions
- Non-multiples cause dimension misalignment

**How It Works**:
```
Pixel Space: 768×1024
    ↓ (VAE Encode, ÷8)
Latent Space: 96×128
    ↓ (Sampling/Processing)
Latent Space: 96×128
    ↓ (VAE Decode, ×8)
Pixel Space: 768×1024
```

## Troubleshooting

### "Must be a multiple of 8" Error

**Problem**: Manual dimensions not divisible by 8

**Solution**:
```python
# Round to nearest multiple of 8
width = (desired_width // 8) * 8
height = (desired_height // 8) * 8
```

**Examples**:
- 770 → 768 (770 // 8 = 96, 96 × 8 = 768)
- 1000 → 1000 (already valid)
- 513 → 512 (513 // 8 = 64, 64 × 8 = 512)

### Out of Memory Errors

**Problem**: VRAM insufficient for selected resolution/batch size

**Solutions**:
1. Reduce resolution to a smaller preset
2. Decrease batch size
3. Use manual mode with smaller dimensions
4. Enable CPU offloading in ComfyUI settings
5. Close other GPU-intensive applications

### Predefined Resolution Not Working

**Problem**: Selected preset doesn't generate expected size

**Solutions**:
1. Check console for parsing errors
2. Verify the preset string hasn't been modified
3. Try manual mode as workaround
4. Report if it's a consistent issue

### Latent Output Incompatible

**Problem**: Generated latent not accepted by downstream nodes

**Solutions**:
1. Verify you're connecting to LATENT input (not IMAGE)
2. Check batch size compatibility
3. Ensure downstream nodes support your resolution
4. Try with a standard ComfyUI sampler first

## Performance Benchmarks

### Generation Time (Empty Latent Creation)

**All resolutions**: < 1ms (negligible overhead)

The latent generation itself is essentially instantaneous. Workflow performance depends on:
- Sampling steps
- Model complexity
- Resolution (affects sampler speed)
- Batch size

### Memory Usage (Approximate)

| Resolution | Batch=1 | Batch=4 | Batch=16 |
|------------|---------|---------|----------|
| 512×512 | ~0.5MB | ~2MB | ~8MB |
| 768×768 | ~1.1MB | ~4.4MB | ~17.6MB |
| 1024×1024 | ~2MB | ~8MB | ~32MB |
| 1536×864 | ~2MB | ~8MB | ~32MB |

**Note**: These are for the latent only. Total VRAM usage includes model weights, VAE, and intermediate activations.

## Compatibility

- **ComfyUI Version**: Any version with latent support
- **Models**: All Stable Diffusion variants (SD 1.5, SD 2.x, SDXL, etc.)
- **Samplers**: All ComfyUI samplers
- **VAEs**: All standard VAE decoders
- **Platforms**: Windows, Linux, macOS

## Advanced Usage

### Calculate Custom Resolutions

For specific aspect ratios not in presets:

```python
# Example: 21:9 ultrawide at ~1000px width
aspect_ratio = 21/9  # 2.333...
target_width = 1008  # Closest multiple of 8 to 1000

height = round(target_width / aspect_ratio / 8) * 8
# height = 432

# Use manual mode: 1008×432
```

### Upscaling Workflow Integration

```
[Latent Generator (512×512)] -> [KSampler (low-res)] 
    -> [VAE Decode] 
    -> [Latent Upscaler] 
    -> [KSampler (high-res)] 
    -> [VAE Decode] 
    -> [Save Image]
```

Start with smaller latent for speed, then upscale for quality.

### A/B Testing Resolutions

```
[Latent Generator A (768×768)]  ──┐
[Latent Generator B (512×768)]  ──┤
[Latent Generator C (1024×576)] ──┴─> [Selector] -> [Same Workflow]
```

Compare same prompt at different aspect ratios.

## Comparison with Standard Empty Latent Image

| Feature | Latent Generator | Standard Empty Latent |
|---------|------------------|----------------------|
| Predefined Resolutions | ✅ 25+ presets | ❌ Manual only |
| Aspect Ratio Labels | ✅ Clear labels | ❌ None |
| Dimension Outputs | ✅ Width/Height | ❌ Latent only |
| Input Validation | ✅ Automatic | ⚠️ Manual check |
| Batch Support | ✅ Yes | ✅ Yes |
| Custom Dimensions | ✅ Yes | ✅ Yes |

## FAQ

**Q: What's the difference between this and the standard Empty Latent Image node?**
A: This node adds predefined resolutions with aspect ratio labels, dimension outputs, and automatic validation for easier workflow setup.

**Q: Can I use decimal values for width/height?**
A: No, dimensions must be integers (whole numbers) and multiples of 8.

**Q: Why are all resolutions multiples of 64?**
A: Because they must be multiples of 8, and common resolutions happen to be multiples of 64 (8×8).

**Q: Does the latent contain any image data?**
A: No, it's initialized with zeros. The sampler adds noise and the model generates the image during sampling.

**Q: Can I use this with SDXL, SD 1.5, and other models?**
A: Yes, it works with any model that uses the standard latent format.

**Q: What's the largest resolution I can generate?**
A: Technically up to 16384×16384, but practical limits depend on your VRAM. Most systems handle up to 2048×2048 comfortably.

**Q: How do I add my own preset resolutions?**
A: You would need to modify the `predefined_resolutions` list in the source code and reload ComfyUI.

**Q: Does batch_size affect image quality?**
A: No, only quantity. Each batch item is independent. Quality depends on resolution, steps, and model.
