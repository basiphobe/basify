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
| `reset_progress` | DROPDOWN | `"false"` | Set to `"true"` to reset and start from the first image. **Automatically toggles back to `"false"` after execution** to prevent accidental re-resets. |

## Output Values

| Output | Type | Description |
|--------|------|-------------|
| `image` | IMAGE | The loaded image tensor (ComfyUI format), or `None` if no image available |
| `mask` | MASK | Alpha channel mask (if present) or zero mask, or `None` if no image available |
| `file_path` | STRING | Full path to the current image file (empty string if no image) |
| `filename` | STRING | Name of the current image file (empty string if no image) |
| `current_index` | INT | Number of images processed so far |
| `total_count` | INT | Total number of images in the directory |
| `completed` | BOOLEAN | `True` when a valid image is available for processing, `False` when no image (finished/errors) |
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

### Completed Flag Behavior

The `completed` output indicates whether a valid image is available in the current execution:
- `completed = True`: A valid image has been loaded and is available for processing
- `completed = False`: No image is available (all processing finished, no images found, or errors occurred)

Downstream nodes should check this flag to determine whether to process the image or skip the current execution.

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

The `reset_progress` parameter provides a convenient way to restart processing from the first image:

**How to Use**:
1. Set `reset_progress` to `"true"` in the node UI
2. Execute the workflow once
3. The parameter **automatically toggles back to `"false"` after execution**

**Why Auto-Toggle?**
The automatic reset prevents a common mistake: if you forget to manually change `reset_progress` back to `"false"`, every subsequent workflow run would reset progress and re-process the first image. The auto-toggle ensures the reset only happens once, when you explicitly request it.

**Alternative Reset Methods**:
- If `reset_on_directory_change` is enabled, simply change the `directory_path` to a different folder
- Manually delete the state file in `py/.directory_states/` for the specific directory

## Wiring Examples

### Example 1: Basic Sequential Processing

The simplest setup - process images one at a time:

```
[Directory Auto Iterator]
    ├─ image → [Your Processing Nodes] → [Save Image]
    ├─ status → [Show Text]
    └─ completed → (not connected - optional monitoring)
```

**Use Case**: Simple batch processing where you want to process every image in a folder.

**Behavior**: 
- Each workflow run processes the next image
- When all images are done, `image` output becomes `None` (may cause downstream errors)
- Monitor `status` output to know when complete

---

### Example 2: Conditional Processing with Completed Flag

**The recommended approach** - use conditional nodes to handle completion:

```
[Directory Auto Iterator]
    ├─ image → [If/Switch Node]
    ├─ completed → [If/Switch Node] (condition input)
    └─ status → [Show Text]

[If/Switch Node]
    ├─ true branch → [Your Processing Nodes] → [Save Image]
    └─ false branch → [Stop/Skip or Notification]
```

**Use Case**: Gracefully handle completion without errors.

**Behavior**:
- When `completed = True`: Image is processed normally
- When `completed = False`: Skip processing or trigger notification
- No errors from downstream nodes receiving `None`

**Example with ComfyUI Built-in Nodes**:
```
[Directory Auto Iterator]
    ├─ image ────────┐
    ├─ completed ────┤
    └─ status ───────┼─→ [Show Text]
                     │
                     ├─→ [If Image Exists] (custom logic)
                     │       ├─ true → [Processing Pipeline]
                     │       └─ false → [Print "All Done"]
```

---

### Example 3: Automated Batch Queue Processing

For fully automated processing of large directories:

```
[Directory Auto Iterator]
    ├─ image → [Processing Nodes] → [Save Image]
    ├─ current_index → [Show Text] ("Progress: X/Y")
    ├─ total_count ──┘
    ├─ completed → [If Node] → (check if False)
    │                    ├─ true → [Stop Queue Node]
    │                    └─ false → (continue)
    └─ status → [Show Text]
```

**Use Case**: Queue up multiple workflow runs and automatically stop when done.

**Behavior**:
- Queue 100+ workflow executions
- Each run processes one image
- When `completed = False`, trigger queue stop
- Remaining queued items are cancelled

**Setup Steps**:
1. Configure your workflow with conditional stop logic
2. Queue the workflow many times (more than total images)
3. The queue will automatically stop when all images are processed

---

### Example 4: Progress Monitoring and Reporting

Track progress with detailed status information:

```
[Directory Auto Iterator]
    ├─ image → [Processing Pipeline]
    ├─ filename → [String Node] → "Currently: {filename}"
    ├─ current_index ──┐
    ├─ total_count ────┤→ [Math Node] → "Progress: {index}/{total} ({percent}%)"
    ├─ completed ──────┤→ [Logic Node] → Status indicator
    └─ status → [Show Text]
```

**Use Case**: Monitor progress in real-time during long batch operations.

**Outputs**:
- Current filename being processed
- Progress percentage
- Overall status
- Completion indicator

---

### Example 5: Multi-Stage Processing with Checkpoints

Process images through multiple stages:

```
[Directory Auto Iterator]
    ├─ image ─────→ [Stage 1: Upscale] ─────→ [Save to temp/]
    │                                              │
    ├─ completed ──→ [Check] ──────────────────────┤
    │                                              │
    └─ status ────→ [Show Text]                    │
                                                    ↓
[Directory Auto Iterator #2]                  (temp/ folder)
    ├─ image ─────→ [Stage 2: Enhance] ─────→ [Save to output/]
    ├─ completed ──→ [Check]
    └─ status ────→ [Show Text]
```

**Use Case**: Multi-pass processing where each stage needs separate iteration.

**Behavior**:
- First iterator processes all images through stage 1
- Second iterator processes stage 1 output through stage 2
- Each stage can be run independently

---

### Example 6: Selective Processing Based on Metadata

Combine with metadata checking:

```
[Directory Auto Iterator]
    ├─ image ────────┬─→ [Get Image Size]
    ├─ file_path ────┤      │
    ├─ completed ────┤      ↓
    └─ status        │   [If Width > 1024]
                     │      ├─ true → [Downscale] → [Save]
                     │      └─ false → [Copy As-Is] → [Save]
                     │
                     └─→ [Check completion]
```

**Use Case**: Only process images that meet certain criteria.

**Behavior**:
- All images are iterated
- Processing varies based on image properties
- Images not meeting criteria are handled differently

---

### Example 7: Error Handling and Logging

Robust setup with error tracking:

```
[Directory Auto Iterator]
    ├─ image ────────→ [Try/Catch Processing]
    │                      ├─ success → [Save to output/]
    │                      └─ error → [Save to errors/]
    ├─ filename ──────→ [Log Node] ("Processing: {filename}")
    ├─ file_path ─────→ [Error Logger] (if processing fails)
    ├─ completed ─────→ [Check if False] → [Generate Report]
    └─ status ────────→ [Show Text] + [Save to log.txt]
```

**Use Case**: Production batch processing with error tracking.

**Behavior**:
- Each image is processed with error handling
- Failed images are logged separately
- Final report generated when `completed = False`
- Full audit trail of processing

---

### Example 8: Notification on Completion

Get notified when batch completes:

```
[Directory Auto Iterator]
    ├─ image ────────→ [Processing Pipeline]
    ├─ completed ────→ [If False]
    │                      ├─ true → [Sound Notifier] (play sound)
    │                      │         [Email Node] (send email)
    │                      │         [Webhook] (notify system)
    │                      └─ false → (continue silently)
    └─ status ───────→ [Show Text]
```

**Use Case**: Long-running batch jobs that complete while you're away.

**Behavior**:
- Images process normally
- When `completed = False` (no more images):
  - Play notification sound
  - Send email alert
  - Trigger external webhook

---

## Understanding the Completed Flag

### ✅ When `completed = True`
- A valid image has been loaded
- `image` and `mask` outputs contain valid tensors
- It's safe to process the image
- The workflow should continue normally

### ❌ When `completed = False`  
- No image is available
- `image` and `mask` outputs are `None`
- One of these conditions occurred:
  - All images have been processed
  - No images found in directory
  - Invalid directory path
  - All remaining images failed to load
- Downstream nodes should skip processing or handle gracefully

### Key Insight
The `completed` flag tells you **"Is there an image ready to process?"** not **"Am I done processing?"**

- `True` = "Yes, process this image"
- `False` = "No image available, skip or stop"

---

## Best Practices for Wiring

### 1. **Always Check the Completed Flag**
Prevent errors by using conditional logic based on `completed`:
```
✅ GOOD: [completed] → [If Node] → Process only when True
❌ BAD:  [image] → [Processing] (will error when image is None)
```

### 2. **Monitor Status Output**
Connect `status` to a display node to see what's happening:
```
[status] → [Show Text] or [Console Print]
```

### 3. **Use Index/Total for Progress**
Calculate progress percentage:
```
[current_index] ──┐
[total_count] ────┤→ [Math: index/total * 100] → "Progress: X%"
```

### 4. **Handle the False Case**
When `completed = False`, decide what to do:
- Stop the queue
- Send notification
- Log completion
- Reset for next batch

### 5. **Test with Small Batches First**
Before processing thousands of images:
- Test with 3-5 images
- Verify the `completed` flag works as expected
- Check that all images are processed
- Confirm graceful completion

---

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

## Quick Integration Example

### Minimal Setup (No Error Handling)
```
[Directory Auto Iterator]
    ├─ image → [Processing] → [Save Image]
    └─ status → [Show Text]
```

### Recommended Setup (With Completion Handling)
```
[Directory Auto Iterator]
    ├─ image ──────────┐
    ├─ completed ──────┤→ [If/Switch Node]
    └─ status ─────────┤       ├─ True → [Processing] → [Save]
                       │       └─ False → [Done Action]
                       └─ [Show Text]
```

See the **Wiring Examples** section above for detailed use cases.

## Technical Notes

### Auto-Toggle Mechanism
The `reset_progress` parameter automatically flips from `"true"` to `"false"` after workflow execution via JavaScript hooks:
- **Hook**: Uses ComfyUI's `onExecutionStart` event in the frontend
- **Timing**: Triggered when the node begins executing; reset occurs 500ms later (after execution completes)
- **Implementation**: Located in `js/directory_auto_iterator.js`
- **Persistence**: The auto-toggled value is saved with the workflow

This ensures the reset is applied exactly once per manual toggle, preventing repetitive resets if you forget to change it back.

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
