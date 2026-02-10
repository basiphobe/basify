# Mask Combiner Node

## Overview
The **Mask Combiner** node provides functionality to merge multiple mask tensors into a single combined mask output in ComfyUI workflows. This node accepts a batch of masks and combines them using various mathematical operations, making it essential for complex masking workflows.

## Features
- **Multiple Combination Modes**: Five different methods to combine masks
- **Batch Processing**: Automatically handles batches of masks
- **Value Safety**: Ensures output values stay in valid mask range [0.0, 1.0]
- **Standard Format**: Uses ComfyUI's standard MASK tensor format

## Inputs

### Required
- **masks** (`MASK`): Input masks to combine
  - Can be a batch of masks with shape `[batch, height, width]`
  - Can be a single mask with shape `[height, width]`
  - All masks in the batch must have the same dimensions

- **combine_mode** (Dropdown): Method for combining masks
  - Options: `union`, `intersection`, `average`, `add`, `multiply`
  - Default: `union`
  - See "Combination Modes" section below for detailed explanations

## Outputs
- **combined_mask** (`MASK`): The combined mask tensor
  - Shape: `[height, width]` (single mask)
  - Values clamped to valid range [0.0, 1.0]
  - Can be used with any node accepting MASK input

## Combination Modes

### Union (Max)
**Operation**: Takes the maximum value at each pixel across all masks

**Use Case**: Combine areas where ANY mask is active (logical OR)

**Example**:
- Mask A: `[0.3, 0.8, 0.1]`
- Mask B: `[0.5, 0.2, 0.9]`
- Result: `[0.5, 0.8, 0.9]`

**Best For**:
- Combining multiple selection areas
- Creating a mask that covers all input regions
- Preserving the strongest signal from any source

### Intersection (Min)
**Operation**: Takes the minimum value at each pixel across all masks

**Use Case**: Find areas where ALL masks overlap (logical AND)

**Example**:
- Mask A: `[0.3, 0.8, 0.1]`
- Mask B: `[0.5, 0.2, 0.9]`
- Result: `[0.3, 0.2, 0.1]`

**Best For**:
- Finding common areas across multiple masks
- Creating restrictive selection zones
- Ensuring all conditions are met

### Average
**Operation**: Averages all mask values at each pixel

**Use Case**: Balanced combination with equal weight to all masks

**Example**:
- Mask A: `[0.4, 0.8, 0.2]`
- Mask B: `[0.6, 0.4, 0.8]`
- Result: `[0.5, 0.6, 0.5]`

**Best For**:
- Creating smooth transitions
- Equal contribution from all sources
- Reducing extreme values

### Add
**Operation**: Sums all mask values, then clamps to [0.0, 1.0]

**Use Case**: Accumulate coverage with emphasis on overlapping areas

**Example**:
- Mask A: `[0.4, 0.8, 0.2]`
- Mask B: `[0.6, 0.4, 0.8]`
- Result: `[1.0, 1.0, 1.0]` (0.4+0.6=1.0, 0.8+0.4=1.2→1.0, 0.2+0.8=1.0)

**Best For**:
- Making overlapping areas more prominent
- Accumulating influence from multiple sources
- Creating strong masks from weak inputs

### Multiply
**Operation**: Multiplies all mask values together at each pixel

**Use Case**: Create conservative masks that require consensus

**Example**:
- Mask A: `[0.5, 1.0, 0.8]`
- Mask B: `[0.6, 0.8, 0.9]`
- Result: `[0.3, 0.8, 0.72]`

**Best For**:
- Creating masks that only activate where all inputs are strong
- Reducing noise by requiring multiple confirmations
- Softening mask edges

## Usage Examples

### Basic Mask Combination
```
Load Image → Image to Mask → ┐
                              ├→ Mask Combiner (union) → combined_mask → Apply Mask
Load Image → Image to Mask → ┘
```

### Multiple Mask Sources
```
CLIPSeg → mask_1 → ┐
                   ├→ Mask Combiner (union) → Mask Blur → Inpaint
SAM → mask_2 ─────→┘
```

### Creating Precise Selections
```
Face Detection → face_mask ──→┐
                               ├→ Mask Combiner (intersection) → precise_mask
Skin Tone Mask → skin_mask ──→┘
```

### Accumulative Masking
```
Edge Detection → edges_1 ──→┐
                            ├→ Mask Combiner (add) → strong_edges → Enhance
Edge Detection → edges_2 ──→┘
```

## Technical Details

### Input Shape Handling
- **Single mask** `[H, W]`: Returns the mask unchanged
- **Batch of masks** `[B, H, W]`: Combines all B masks into one `[H, W]` mask
- **Single batch** `[1, H, W]`: Extracts and returns the single mask

### Value Range
- All output values are guaranteed to be in the range [0.0, 1.0]
- `add` mode explicitly clamps values
- Other modes naturally stay within range due to their operations

### Performance Considerations
- All operations use optimized PyTorch tensor operations
- Memory usage scales with mask dimensions and batch size
- Very large batches (100+ masks) may take longer to process

## Tips and Best Practices

1. **Mode Selection**:
   - Use `union` when you want coverage from any source
   - Use `intersection` when you need strict overlap
   - Use `average` for balanced, smooth results
   - Use `add` to emphasize overlapping regions
   - Use `multiply` for conservative, high-confidence masks

2. **Workflow Integration**:
   - Combine masks from different detection methods for better results
   - Use with Mask Blur for smoother edges after combination
   - Chain multiple combiners for complex logic (e.g., (A ∪ B) ∩ C)

3. **Quality Optimization**:
   - Pre-process masks (blur, threshold) before combining
   - Consider the order of operations in multi-stage combinations
   - Test different modes to find what works best for your use case

4. **Common Patterns**:
   - **Failsafe masking**: Union multiple detection methods
   - **Precision masking**: Intersect broad mask with detail mask
   - **Soft transitions**: Average multiple gradients
   - **Noise reduction**: Multiply similar masks to reduce false positives

## Common Issues

### Output is All White or All Black
- **Cause**: Using `intersection` with non-overlapping masks (→ black) or `add` with many bright masks (→ white)
- **Solution**: Try `union` or `average` mode, or adjust input masks

### Masks Not Combining as Expected
- **Cause**: Input masks may be in different value ranges
- **Solution**: Normalize masks to [0.0, 1.0] before combining

### Single Mask Output Looks Wrong
- **Cause**: Only one mask in the batch, operations may not make sense
- **Solution**: Node returns single masks unchanged; check your upstream nodes

## Version History
- **v1.0.0**: Initial release with five combination modes

## Related Nodes
- **Image to Mask**: Convert images to masks for combining
- **Mask to Image**: Visualize combined masks
- **Mask Blur**: Soften mask edges after combination
- **Inpaint**: Use combined masks for inpainting operations
- **Mask Composite**: Apply combined masks to images
