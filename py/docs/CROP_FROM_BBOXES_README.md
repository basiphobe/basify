# BasifyCropFromBBoxes

A ComfyUI custom node that crops images based on bounding boxes with optional padding and clamping.

## Features

- **Flexible Input Formats**: Accepts bounding boxes as numpy/torch arrays, Python lists, or JSON strings
- **Automatic Padding**: Add configurable padding around each bounding box
- **Boundary Clamping**: Optional clamping to keep crops within image boundaries
- **Batch Output**: Returns all crops as a uniform batch (padded to max dimensions)
- **Metadata Export**: Provides detailed JSON metadata for each crop including coordinates and dimensions

## Inputs

### Required

- **image** (`IMAGE`): Input image tensor in ComfyUI format `[B,H,W,C]`
  - Currently supports single images (batch_size=1)
  
- **bboxes** (`*`): Bounding boxes in one of these formats:
  - Numpy/torch array: `[N,4]` or `[1,N,4]` shaped as `[x1,y1,x2,y2]`
  - Python list: `[[x1,y1,x2,y2], ...]`
  - JSON string: `"[[x1,y1,x2,y2], ...]"`
  
- **pad_percent** (`FLOAT`, default: `0.35`): Padding to add around each bbox as a percentage of its size
  - Range: `0.0` to `1.0`
  - Example: `0.35` adds 35% padding, expanding a 200x200 box to 270x270
  
- **clamp_to_image** (`BOOLEAN`, default: `True`): Clamp crop regions to stay within image boundaries
  
- **round_to_int** (`BOOLEAN`, default: `True`): Round crop coordinates to integers
  
- **min_size** (`INT`, default: `16`): Minimum allowed crop width/height after clamping
  - Range: `1` to `4096`

### Optional

- **max_crops** (`INT`, default: `0`): Maximum number of crops to process
  - `0` = no limit
  - Range: `0` to `1000`

## Outputs

- **crops** (`IMAGE`): Batch of cropped images `[N,H,W,C]`
  - All crops padded to the maximum dimensions in the batch
  - Maintains ComfyUI's image format (torch tensor, float, 0..1 range)
  
- **crop_rects** (`STRING`): JSON array containing metadata for each crop:
  ```json
  [
    {
      "x": 65.0,           // Top-left X coordinate
      "y": 165.0,          // Top-left Y coordinate
      "w": 270.0,          // Crop width
      "h": 270.0,          // Crop height
      "x1": 65.0,          // Left edge
      "y1": 165.0,         // Top edge
      "x2": 335.0,         // Right edge
      "y2": 435.0,         // Bottom edge
      "cx": 200.0,         // Center X
      "cy": 300.0,         // Center Y
      "pad_percent": 0.35  // Applied padding
    }
  ]
  ```

## Behavior

### Crop Calculation

For each bounding box `[x1, y1, x2, y2]`:

1. Calculate original dimensions:
   - `w = x2 - x1`
   - `h = y2 - y1`

2. Apply padding:
   - `w2 = w × (1 + pad_percent)`
   - `h2 = h × (1 + pad_percent)`

3. Calculate center and new top-left:
   - `cx = (x1 + x2) / 2`
   - `cy = (y1 + y2) / 2`
   - `x = cx - w2 / 2`
   - `y = cy - h2 / 2`

4. Apply optional rounding and clamping

### Example

Input bbox: `[100, 200, 300, 400]` with `pad_percent=0.35`:

```
Original: w=200, h=200
Padded: w2=270, h2=270
Center: cx=200, cy=300
Crop: x=65, y=165, size=(270, 270)
```

### Batch Consistency

All crops are padded to match the largest crop dimensions in the batch, ensuring a uniform tensor output that ComfyUI can process as a batch.

## Error Handling

The node includes robust error handling for:

- Empty bbox lists
- Invalid bbox formats (non-numeric, wrong shape)
- Invalid coordinates (x2 ≤ x1 or y2 ≤ y1)
- Multi-image batches (currently raises clear error)
- Crops smaller than `min_size`

## Usage Example

```python
# Example bounding boxes from a detector
bboxes = [
    [100, 200, 300, 400],  # Face 1
    [450, 150, 600, 350],  # Face 2
]

# Or as JSON string
bboxes_json = "[[100, 200, 300, 400], [450, 150, 600, 350]]"

# Connect to the node:
# - image: your source image
# - bboxes: detection results
# - pad_percent: 0.35 (adds 35% padding)
# - Result: batch of 2 cropped face images
```

## Integration

This node works well with:

- Object detection nodes that output bounding boxes
- Face detection pipelines
- Any workflow requiring extraction of specific image regions
- Downstream processing that needs crop metadata for reconstruction

## Logging

The node logs helpful debug information:
- Number of bboxes being processed
- Image dimensions and padding settings
- Individual crop calculations and dimensions
- Final batch size

Enable debug logging to see detailed crop calculations during processing.
