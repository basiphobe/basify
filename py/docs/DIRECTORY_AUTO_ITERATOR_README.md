# Directory Auto Iterator

## Overview

The **Directory Auto Iterator** is a ComfyUI custom node that automatically processes all images in a directory sequentially, one image per workflow execution. It maintains state between runs, tracks which images have been processed, and automatically stops when all images are complete.

## Key Features

- **Automatic Iteration**: Processes one image per workflow execution without manual intervention
- **State Persistence**: Remembers which images have been processed across ComfyUI restarts
- **Recursive Scanning**: Optional subdirectory processing
- **Progress Tracking**: Provides detailed status information about processing progress
- **Robust Error Handling**: Skips corrupted or missing images and continues processing
- **Dynamic Updates**: Detects new or removed images in the directory

## Node Information

- **Node Name**: `BasifyDirectoryAutoIterator`
- **Display Name**: `Basify: Directory Auto Iterator`
- **Category**: `basify`

## Input Parameters

### Required Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `directory_path` | STRING | `""` | Path to the directory containing images to process |
| `process_subdirectories` | DROPDOWN | `"disable"` | Whether to include subdirectories (`enable`/`disable`) |
| `reset_on_directory_change` | DROPDOWN | `"enable"` | Reset to first image when directory path changes (`enable`/`disable`) |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reset_progress` | DROPDOWN | `"false"` | Set to `"true"` to reset and start from the first image |

## Output Values

| Output | Type | Description |
|--------|------|-------------|
| `image` | IMAGE | The loaded image tensor (ComfyUI format) |
| `mask` | MASK | Alpha channel mask (if present) or zero mask |
| `file_path` | STRING | Full path to the current image file |
| `filename` | STRING | Name of the current image file |
| `current_index` | INT | Number of images processed so far |
| `total_count` | INT | Total number of images in the directory |
| `completed` | BOOLEAN | `True` when all images have been processed |
| `status` | STRING | Human-readable status message |

## Supported Image Formats

- `.jpg`, `.jpeg`
- `.png`
- `.bmp`
- `.tiff`, `.tif`
- `.webp`
- `.gif`

## How It Works

### State Management

The node maintains a state file for each directory being processed. State files are stored in:
```
py/.directory_states/directory_state_<sanitized_path>.json
```

State information includes:
- List of processed files
- Directory path
- Completion status

### Processing Flow

1. **Directory Scan**: On each execution, the node scans the directory for images
2. **State Check**: Loads the state to determine which images have been processed
3. **Next Image**: Selects the next unprocessed image
4. **Load Image**: Loads the image and converts it to ComfyUI tensor format
5. **Update State**: Marks the image as processed and saves the state
6. **Return Data**: Outputs the image and metadata

### Automatic Re-execution

The node uses the `IS_CHANGED` method to return a random value on each check, forcing ComfyUI to re-execute the node every time the workflow runs. This enables automatic iteration through all images.

## Usage Examples

### Basic Usage

1. Add the **Basify: Directory Auto Iterator** node to your workflow
2. Set `directory_path` to the folder containing your images
3. Connect the `image` output to your processing nodes
4. Run the workflow repeatedly (manually or with queue/batch processing)

Each execution will automatically process the next image in sequence.

### Processing Subdirectories

```
directory_path: /path/to/images
process_subdirectories: enable
```

This will process all images in the directory and all subdirectories, sorted alphabetically.

### Resetting Progress

To start over from the first image:
- Set `reset_progress` to `"true"`
- Execute the workflow once
- Change `reset_progress` back to `"false"`

Alternatively, if `reset_on_directory_change` is enabled, simply change the `directory_path`.

### Conditional Workflow Logic

Use the `completed` output to control workflow behavior:

```python
# Example: Only run processing nodes if not completed
if not completed:
    # Process image
    pass
else:
    # All images processed, stop or trigger notification
    pass
```

## Status Messages

| Status | Meaning |
|--------|---------|
| `"Processing: <filename> (X/Y processed, Z remaining)"` | Currently processing an image |
| `"All images processed. Processed X total images."` | All images complete |
| `"No images found in directory"` | Directory is empty or contains no supported images |
| `"Invalid directory path"` | The specified directory doesn't exist |
| `"All remaining images failed to load. Processed X/Y images."` | Remaining images are corrupted or unreadable |

## Error Handling

The node handles several error conditions gracefully:

- **Missing Files**: If a file is deleted between scans, it's marked as processed and skipped
- **Corrupted Images**: Failed image loads are logged and skipped
- **Invalid Directory**: Returns error status without crashing
- **Empty Directory**: Returns appropriate status message

## Best Practices

### 1. Use Absolute Paths
Always provide absolute paths to directories to avoid confusion.

### 2. Monitor Status Output
Connect the `status` output to a display node to track progress.

### 3. Check Completion Flag
Use the `completed` output to trigger actions when all images are processed:
- Send notifications
- Stop batch processing
- Archive processed images

### 4. Batch Processing Setup
For automated processing of large directories:
1. Set up your workflow with the Directory Auto Iterator
2. Use ComfyUI's queue system to run the workflow repeatedly
3. Monitor the `completed` flag to know when to stop

### 5. State File Management
State files persist across sessions. To completely reset:
- Delete files in `py/.directory_states/`
- Or use the `reset_progress` parameter

### 6. Dynamic Directories
The node re-scans the directory on each execution, so you can:
- Add new images during processing (they'll be picked up)
- Remove images (they'll be skipped if already processed)

## Troubleshooting

### Images Not Processing
- Verify the directory path exists
- Check that images have supported extensions
- Ensure file permissions allow reading

### State Not Saving
- Check write permissions for `py/.directory_states/` directory
- Look for error messages in the console

### Stuck on Same Image
- Try setting `reset_progress` to `"true"` and running once
- Check if the state file is corrupted (delete and restart)

### Subdirectories Not Scanned
- Ensure `process_subdirectories` is set to `"enable"`
- Verify subdirectories contain images with supported extensions

## Integration Example

```
[Directory Auto Iterator] -> [Image Processing Nodes] -> [Save Image]
                          |
                          +-> [status] -> [String Display]
                          +-> [completed] -> [Conditional Logic]
```

## Technical Notes

### Image Loading
- Images are loaded using PIL (Pillow)
- EXIF orientation is automatically handled
- All images are converted to RGB format
- Output tensor shape: `[1, H, W, 3]` (batch, height, width, channels)

### Mask Generation
- If image has an alpha channel, it's extracted as the mask
- Mask values are inverted (1.0 = transparent)
- If no alpha channel, a zero mask is generated

### State File Format
```json
{
  "processed_files": [
    "/path/to/image1.jpg",
    "/path/to/image2.png"
  ],
  "directory_path": "/path/to/images",
  "completed": false
}
```

## Compatibility

- Compatible with standard ComfyUI image processing nodes
- Output format matches ComfyUI's `LoadImage` node
- Works with any workflow that accepts IMAGE and MASK inputs

## Performance Considerations

- Directory scanning is performed on each execution (minimal overhead)
- State files are small JSON files (negligible disk usage)
- Image loading time depends on image size and format
- Processing speed limited by workflow execution, not the iterator

## Migration from Index-Based System

Older versions used an index-based system. The current version uses filename-based tracking for better reliability when files are added or removed. Old state files are automatically migrated on first use.
