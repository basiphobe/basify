# Batch Selector Node

## Overview
The **Batch Selector** node provides functionality to select a specific item from a batch in ComfyUI workflows. This node works with any batch type including images, masks, latents, and more. It uses simple index-based selection with support for negative indexing.

## Features
- **Universal Batch Support**: Works with IMAGE, MASK, LATENT, and other batch types
- **Negative Indexing**: Python-style negative indices (-1 for last, -2 for second-to-last, etc.)
- **Type Preservation**: Output type automatically matches input type
- **Safe Bounds Checking**: Validates index ranges with helpful error messages
- **Simple Interface**: Single index input - no complex mode selection needed

## Inputs

### Required
- **batch** (`IO.ANY`): Input batch to select from
  - Can be IMAGE with shape `[batch, height, width, channels]`
  - Can be MASK with shape `[batch, height, width]`
  - Can be LATENT dict with `{"samples": tensor}`
  - Works with any batch-compatible type
  - Standard ComfyUI formats

- **index** (`INT`): Index of the item to select
  - Default: `0` (first item)
  - Range: `-10000` to `10000`
  - Supports negative indexing (Python-style)
  - Zero-based indexing (first item is index 0)
  - Examples:
    - `0` = first item
    - `-1` = last item
    - `-2` = second-to-last item
    - `5` = sixth item

## Outputs
- **output** (`IO.ANY`): The selected item
  - Type automatically matches input type
  - If input is IMAGE batch, output is single IMAGE
  - If input is MASK batch, output is single MASK
  - If input is LATENT batch, output is single LATENT
  - Maintains proper batch dimension (size 1)

## How It Works

The node automatically detects the input type and selects the item at the specified index:

1. **Type Detection**: Determines if input is IMAGE, MASK, LATENT, or other type
2. **Index Resolution**: Converts negative indices to positive (e.g., -1 → last index)
3. **Bounds Checking**: Validates that index is within valid range
4. **Selection**: Extracts the item at the specified index
5. **Output**: Returns item maintaining batch dimension for compatibility

## Usage Examples

### Example 1: Get First Image
Select the first image from a batch:
```
Load Image Batch → Batch Selector (index: 0) → Save Image
```

### Example 2: Get Last Mask
Extract the last mask from a batch:
```
Mask Batch → Batch Selector (index: -1) → Apply Mask
```

### Example 3: Select Specific Item
Pick the third image (index 2) from a batch:
```
Image Batch → Batch Selector (index: 2) → Process...
```

### Example 4: Second-to-Last
Get the second-to-last latent:
```
Latent Batch → Batch Selector (index: -2) → VAE Decode
```

## Indexing Rules

### Positive Indexing (0-based)
- `0` = first item
- `1` = second item
- `2` = third item
- etc.

### Negative Indexing (from end)
- `-1` = last item
- `-2` = second-to-last item
- `-3` = third-to-last item
- etc.

### Valid Range
For a batch of size N:
- Positive indices: `0` to `N-1`
- Negative indices: `-N` to `-1`

## Error Handling

### Single Item Input
If only one item is provided, that item is returned regardless of index (unless index is out of bounds).

### Index Out of Bounds
If the specified index is outside the valid range:
- Error message shows: requested index, batch size, and valid range
- Example: "Index 10 is out of bounds for batch size 5. Valid range: -5 to 4"

### Invalid Shape
If input batch doesn't have expected format:
- Error message shows: actual shape and expected format
- Works for IMAGE (4D), MASK (3D), and LATENT (dict with "samples")

## Technical Details

### Type Detection
- **LATENT**: Detected as `dict` with `"samples"` key
- **IMAGE**: Detected as 4D tensor `[batch, height, width, channels]`
- **MASK**: Detected as 3D tensor `[batch, height, width]`

### Batch Dimension Preservation
- Selected items maintain batch dimension (size 1)
- IMAGE: Returns `[1, height, width, channels]`
- MASK: Returns `[1, height, width]`
- LATENT: Returns `{"samples": [1, ...]}`

This ensures compatibility with downstream nodes expecting batch inputs.

### Performance
- Minimal computational overhead
- No image processing, only indexing
- Fast execution regardless of batch size

### Logging
- Info logging shows selection details
- Helpful for troubleshooting workflows
- Color-coded console output for visibility

## Tips and Best Practices

1. **Use 0 and -1 for Common Cases**: Most common needs are first (0) or last (-1) item

2. **Negative Indexing is Flexible**: Use `-1` for last, `-2` for second-to-last - works regardless of batch size

3. **Error Messages are Helpful**: If you get an index error, the message tells you exactly what range is valid

4. **Works with Any Batch**: Not limited to images - works with masks, latents, and any batch-structured data

5. **No Mode Selection Needed**: Simple index input makes it easy to understand and use

6. **Combine with Batch Generators**: Works great after nodes that generate batches (e.g., animation frames, variations)

## Category
**basify** - Part of the Basify custom node collection

## Node Name
- **Class Name**: `BasifyBatchSelector`
- **Display Name**: `Basify: Batch Selector`
