# Batch Image Processing with External Script

This guide shows how to process multiple images through your ComfyUI workflow using an external Python script instead of the built-in DirectoryAutoIterator.

## Why Use External Batch Processing?

**Advantages:**
- Full control over iteration from outside ComfyUI
- No need for "Run Instant" mode
- Clean start/stop behavior
- Easy to integrate with other automation
- Can pass images as command-line arguments
- Better for CI/CD pipelines

## Setup Instructions

### 1. Export Your Workflow in API Format

The batch processor needs your workflow in **API format**, not UI format.

**In ComfyUI:**
1. Open your workflow
2. Click the ⚙️ (settings/menu) icon
3. Select **"Save (API Format)"** or **"Export (API Format)"**  
4. Save as `workflow_api.json`

**Alternatively,** use the developer console:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Type: `app.graphToPrompt()`
4. Copy the output JSON
5. Save it as `workflow_api.json`

### 2. Find Your LoadImage Node ID

Open your workflow JSON and find the LoadImage node. It will look like:

```json
{
  "1234": {
    "inputs": {
      "image": "example.png",
      "upload": "image"
    },
    "class_type": "LoadImage",
    ...
  }
}
```

The `1234` is your **node ID** - you'll need this for the script.

**Quick way to find it:**
```bash
grep -B 2 '"class_type": "LoadImage"' your_workflow.json | grep -o '^  "[0-9]*"' | tr -d ' "'
```

### 3. Install Dependencies

```bash
pip install requests websocket-client
```

## Usage

### Basic Usage

**First, export your workflow in API format!**

```bash
./batch_process_images.py \
  /path/to/workflow_api.json \
  /path/to/images/directory \
  --image-node-id 1234
```

### Example

```bash
# 1. Export workflow from ComfyUI UI as API format
# 2. Then run:
./batch_process_images.py \
  ~/Downloads/workflow_api.json \
  ~/photos \
  --image-node-id 1691
```

### Advanced Options

```bash
# Specify custom server address
./batch_process_images.py \
  workflow.json \
  images/ \
  --image-node-id 1234 \
  --server 192.168.1.100:8188

# Process only specific image formats
./batch_process_images.py \
  workflow.json \
  images/ \
  --image-node-id 1234 \
  --extensions .png .jpg
```

## Command-Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `workflow` | Yes | Path to your ComfyUI workflow JSON file |
| `image_dir` | Yes | Directory containing images to process |
| `--image-node-id` | Yes | ID of the LoadImage node (e.g., "1234") |
| `--server` | No | ComfyUI server address (default: 127.0.0.1:8188) |
| `--extensions` | No | Image extensions to process (default: .jpg .jpeg .png .bmp .tiff .tif .webp) |

## How It Works

1. **Script scans** the image directory for valid image files
2. **For each image:**
   - Uploads the image to ComfyUI
   - Updates the workflow JSON with the uploaded image filename
   - Queues the workflow for execution
   - Waits for completion
   - Moves to the next image
3. **Reports progress** and completion status

## Example Output

```
Found 10 images to process

[1/10] Processing: image001.png
  📋 Queued with prompt ID: abc123...
  ✅ Completed successfully

[2/10] Processing: image002.png
  📋 Queued with prompt ID: def456...
  ✅ Completed successfully

...

🎉 Batch processing complete! Processed 10 images.
```

## Integration with Your Wildcard System

The script works perfectly with your wildcard processor! Each queued workflow execution will:
- Generate new random wildcard values
- Process the current image
- Complete cleanly

Since iteration is controlled externally, there's no infinite loop issue.

## Troubleshooting

**"Image node ID not found"**
- Double-check the node ID from your workflow JSON
- Make sure you're using the LoadImage node ID, not another node

**"No images found in directory"**
- Verify the directory path is correct
- Check file extensions match (use `--extensions` if needed)

**"Failed to upload image"**
- Ensure ComfyUI is running
- Check the server address with `--server`

**"Execution timed out"**
- Your workflow may be taking longer than 5 minutes per image
- This is just a warning; check ComfyUI UI for actual status

## Advanced: Programmatic Usage

You can also import the processor class in your own Python scripts:

```python
from batch_process_images import ComfyUIBatchProcessor
from pathlib import Path

processor = ComfyUIBatchProcessor(server_address="127.0.0.1:8188")

processor.process_images(
    workflow_path=Path("workflow.json"),
    image_dir=Path("images/"),
    image_node_id="1234"
)
```

## Comparison: Iterator vs External Script

| Feature | DirectoryAutoIterator | External Script |
|---------|----------------------|-----------------|
| Setup | Add node to workflow | Modify workflow + run script |
| Control | Internal to ComfyUI | External CLI/script |
| Stop behavior | Needs IS_CHANGED logic | Natural loop end |
| Integration | ComfyUI only | Any automation system |
| Progress tracking | Logs only | Script output + logs |
| Flexibility | Fixed iteration | Fully customizable |

Choose **DirectoryAutoIterator** for simple workflows within ComfyUI.  
Choose **External Script** for automation, CI/CD, or complex iteration logic.
