# Save Image (Custom Path) - Documentation

A powerful ComfyUI node for saving images with dynamic paths, customizable filenames, and comprehensive metadata support.

## Features

- **Dynamic Path Variables** - Use variables in folder paths and filenames
- **Session Persistence** - Keep random values consistent across multiple saves
- **Batch Processing** - Automatically handles multiple images
- **Metadata Embedding** - Preserve workflow information in saved files
- **Thread-Safe** - Prevents file conflicts in concurrent workflows
- **Text File Export** - Optionally save text content alongside images

---

## Input Parameters

### Required Inputs

#### `image` (IMAGE)
The image tensor to save. Supports batch processing.

#### `custom_folder` (STRING)
Destination folder path. Supports dynamic variables.

**Default:** `output/comfy/{date}`

**Examples:**
```
/llm/output/comfy/{date}
/llm/output/comfy/{date}/{time}
/llm/output/comfy/{year}/{month}/{day}
/llm/output/renders/{date}/{uuid}
/llm/output/{datetime}/{random_string}
```

#### `filename_prefix` (STRING)
Prefix for the saved filename. Supports variables and Python format strings.

**Default:** `generated_image_{date}_{time}`

**Examples:**
```
generated_image_{date}_{time}  # Default with timestamp
render_{random_number}          # With random value
portrait_{uuid}                 # With UUID
image_{:06d}                    # Counter mode: 000000, 000001, 000002...
frame_{:04d}                    # Counter mode: 0000, 0001, 0002...
{date}_img_{:03d}               # Combine timestamp and counter
```

#### `file_extension` (DROPDOWN)
Output file format.

**Options:** `png`, `jpg`, `webp`  
**Default:** `png`

- **PNG** - Lossless, supports full metadata
- **JPG** - Smaller file size, 95% quality
- **WEBP** - Modern format, good compression

#### `save_metadata` (DROPDOWN)
Embed workflow metadata in the saved image.

**Options:** `enable`, `disable`  
**Default:** `enable`

When enabled, saves ComfyUI workflow data that allows you to load the image back into ComfyUI and recover the full workflow.

#### `save_text` (DROPDOWN)
Enable/disable text file saving.

**Options:** `enable`, `disable`  
**Default:** `disable`

When enabled with `text_content`, creates a `.txt` file with the same name as the image.

### Optional Inputs

#### `text_content` (STRING)
Text content to save alongside the image.

**Default:** Empty string  
**Multiline:** Yes

Useful for saving prompts, descriptions, or generation parameters.

**Example:**
```
Output:
  - image.png
  - image.txt
```

#### `session_id` (STRING)
Custom session identifier for persisting random values.

**Default:** Empty (uses node's unique_id automatically)

**Use Cases:**
- Share random values across multiple save nodes
- Create consistent folder structures
- Force new random values by changing session_id
- Group related saves with meaningful IDs

---

## Path Variables

All variables can be used in both `custom_folder` and `filename_prefix`.

### Date & Time Variables

| Variable | Format | Example | Description |
|----------|--------|---------|-------------|
| `{date}` | YYYY-MM-DD | 2025-12-27 | Current date |
| `{time}` | HH-MM-SS | 14-30-45 | Current time |
| `{datetime}` | YYYY-MM-DD_HH-MM-SS | 2025-12-27_14-30-45 | Combined date and time |
| `{timestamp}` | Unix timestamp | 1735315845 | Seconds since epoch |
| `{year}` | YYYY | 2025 | Current year |
| `{month}` | MM | 12 | Current month |
| `{day}` | DD | 27 | Current day |
| `{hour}` | HH | 14 | Current hour (24h) |
| `{minute}` | MM | 30 | Current minute |
| `{second}` | SS | 45 | Current second |

### Random Variables (Persisted per Session)

| Variable | Format | Example | Description |
|----------|--------|---------|-------------|
| `{uuid}` | 8 characters | a3f7b2c1 | First 8 chars of UUID4 |
| `{random_number}` | 6 digits | 847592 | Random number (100000-999999) |
| `{random_string}` | 8 chars | x7k2p9q4 | Lowercase alphanumeric |

**Important:** Random values persist per session! See [Session Persistence](#session-persistence) below.

---

## Counter Formatting (Auto-Increment Mode)

When a Python format string like `{:06d}` is detected in either `custom_folder` OR `filename_prefix`, the node automatically switches to counter mode and generates sequential filenames.

### Python Format Strings

Use Python format strings for explicit control over counter padding. They work in both paths and filenames:

| Format | Description | Example Output |
|--------|-------------|----------------|
| `{:04d}` | 4-digit padding | `image_0000.png`, `image_0001.png`, `image_9999.png` |
| `{:06d}` | 6-digit padding | `image_000000.png`, `image_000001.png` |
| `{:08d}` | 8-digit padding | `image_00000000.png`, `image_00000001.png` |
| `{:d}` | No padding | `image_0.png`, `image_1.png`, `image_123.png` |

**Example Usage:**
```yaml
# Counter in filename
filename_prefix: frame_{:06d}
custom_folder: /output/{date}

Output:
  /output/2025-12-28/frame_000000.png
  /output/2025-12-28/frame_000001.png
  /output/2025-12-28/frame_000002.png

# Counter in folder path
filename_prefix: image
custom_folder: /output/batch_{:04d}

Output:
  /output/batch_0000/image.png
  /output/batch_0001/image.png
  /output/batch_0002/image.png
```

### Auto-Detection Mode

If no format string is provided, the node automatically determines padding width:
- **Default:** 3 digits minimum (`001`, `002`, `003`, ...)
- **Adaptive:** Expands when needed (at `1000` switches to `1000`, `1001`, ...)
- **Smart:** Scans existing files to maintain consistency

**Example:**
```yaml
filename_prefix: image
use_timestamp: disable

Output with auto-padding:
  image_001.png
  image_002.png
  ...
  image_999.png
  image_1000.png  ← Automatically expands to 4 digits
  image_1001.png
```

This ensures you never run out of counter space, even with large batches.

---

## Session Persistence

Random variables (`{uuid}`, `{random_number}`, `{random_string}`) are automatically persisted to ensure consistent folder structures across multiple saves.

### Automatic Persistence (Default Behavior)

When `session_id` is left empty, the node's internal `unique_id` is used as the session identifier.

**Example Workflow:**
```
Path: /llm/output/{date}/{uuid}

Image 1 saved to: /llm/output/2025-12-27/a3f7b2c1/
Image 2 saved to: /llm/output/2025-12-27/a3f7b2c1/  ← Same UUID!
Image 3 saved to: /llm/output/2025-12-27/a3f7b2c1/
```

All images from the same node instance go to the same folder.

### Manual Session Control

Set a custom `session_id` to control random value behavior:

**Example 1: Share Random Values Across Multiple Nodes**
```
Node A: session_id = "my_project"
Node B: session_id = "my_project"

Both nodes will use the same {uuid}, {random_number}, etc.
```

**Example 2: Force New Random Values**
```
First workflow: session_id = "batch_1"
Second workflow: session_id = "batch_2"

Different session_ids = different random values
```

**Example 3: Organized Project Structure**
```
session_id = "portrait_series_2025"
Path: /projects/{session_id}/{date}/{uuid}

Result: /projects/portrait_series_2025/2025-12-27/a3f7b2c1/
```

---

## Batch Processing

The node automatically handles multiple images in a batch.

**Batch Size: 4 images**
```
Output:
  generated_image_2025-12-27_14-30-45_batch1.png
  generated_image_2025-12-27_14-30-45_batch2.png
  generated_image_2025-12-27_14-30-45_batch3.png
  generated_image_2025-12-27_14-30-45_batch4.png
```

Batch suffix is only added when processing multiple images.

---

## Complete Examples

### Example 1: Daily Organized Renders
```yaml
custom_folder: /renders/{year}/{month}/{day}
filename_prefix: render
use_timestamp: enable
session_id: (empty)

Output: /renders/2025/12/27/render_2025-12-27_14-30-45.png
```

### Example 2: Project-Based with Random Folders
```yaml
custom_folder: /projects/portraits/{date}/{uuid}
filename_prefix: portrait_{random_number}
use_timestamp: disable
session_id: portraits_batch_1

Output: /projects/portraits/2025-12-27/a3f7b2c1/portrait_847592_001.png
```

### Example 3: Time-Stamped Sequences
```yaml
custom_folder: /output/{datetime}
filename_prefix: frame
use_timestamp: enable
session_id: (empty)

Output: /output/2025-12-27_14-30-45/frame_2025-12-27_14-30-45.png
```

### Example 4: Random Subfolder Organization
```yaml
custom_folder: /llm/output/comfy/{date}/{random_string}
filename_prefix: img_{time}
use_timestamp: disable
session_id: daily_run

Output: /llm/output/comfy/2025-12-27/x7k2p9q4/img_14-30-45_001.png
```

### Example 5: With Text Export
```yaml
custom_folder: /outputs/{date}
filename_prefix: generated
file_extension: png
save_text: enable
text_content: "Prompt: A beautiful sunset over mountains"

Output:
  /outputs/2025-12-27/generated_2025-12-27_14-30-45.png
  /outputs/2025-12-27/generated_2025-12-27_14-30-45.txt
```

---

## Metadata Support

### PNG Format (Full Workflow Support ✓)

When `save_metadata = enable` and using PNG format, the node embeds workflow data **exactly like ComfyUI's native SaveImage node**:
- Full ComfyUI workflow information
- Node configuration and connections
- All prompt data

**Drag-and-Drop Support:** ✓ Images can be dragged back into ComfyUI to fully restore the workflow.

### JPG/WEBP Format (No Workflow Support)

JPG and WEBP formats **do not support** ComfyUI workflow embedding. These formats cannot be used for drag-and-drop workflow restoration.

**Recommendation:** Always use PNG format when you need to preserve and reload workflows.

---

## Thread Safety

The node uses locking mechanisms to prevent file conflicts when:
- Multiple workflows run simultaneously
- Batch processing occurs
- Same folder paths are used

This ensures no corrupted saves or race conditions.

---

## Output

The node returns:

1. **IMAGE** - The original image tensor (passthrough)
2. **STRING** - Saved file path(s)
   - Single image: `/path/to/image.png`
   - Batch: `/path/img1.png;/path/img2.png;/path/img3.png`

The path output can be used by downstream nodes for further processing.

---

## Tips & Best Practices

### 1. Use Session IDs for Multi-Node Consistency
```
Set the same session_id on all save nodes in a workflow to ensure 
they all use the same {uuid} and save to the same folder structure.
```

### 2. Organize by Date for Easy Management
```
/outputs/{year}/{month}/{day}

Creates automatic calendar-based organization:
  /outputs/2025/12/27/
  /outputs/2025/12/28/
```

### 3. Combine Variables for Unique Folders
```
/renders/{date}_{uuid}

Each day's renders go to a unique subfolder:
  /renders/2025-12-27_a3f7b2c1/
  /renders/2025-12-28_x8k9m2n4/
```

### 4. Use Random Strings for Experiments
```
/experiments/{random_string}

Each run creates a new experiment folder:
  /experiments/x7k2p9q4/
```

### 5. Use Counter Mode for Sequences
```
filename_prefix: frame_{:06d}

Creates zero-padded sequential files (great for video frames):
  frame_000000.png
  frame_000001.png
  frame_000002.png
  ...
  frame_001234.png

Works in folders too:
  custom_folder: /output/render_{:04d}
  → /output/render_0000/, /output/render_0001/, etc.
```

### 6. Save Prompts with Text Export
```
save_text: enable
text_content: {your_prompt_text}

Great for keeping prompts alongside generated images
for reference and documentation.
```

---

## Troubleshooting

### Issue: Random values change every save
**Solution:** Make sure you're using the same node instance, or set a custom `session_id`.

### Issue: Folder not created
**Solution:** Ensure the parent directory exists and you have write permissions. The node creates folders recursively but needs permission.

### Issue: Metadata not loading in ComfyUI
**Solution:** Use PNG format for full metadata support. JPG/WEBP have limited metadata capacity.

### Issue: Batch suffix appearing with single image
**Solution:** This shouldn't happen. Check if your input is actually a batch tensor with shape [B, H, W, C] where B > 1.

---

## Node Display Name

`Save Image (Auto-Increment + Timestamp + Metadata + Thread-Safe)`

---

## Category

`basify`

---

## Version History

- **v2.1** - Optimized code, removed unused methods, fixed workflow drag-and-drop support
- **v2.0** - Added dynamic path variables and session persistence
- **v1.0** - Initial release with custom paths and metadata support
