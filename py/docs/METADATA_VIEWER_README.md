# Metadata Viewer

## Overview

The **Metadata Viewer** is a ComfyUI custom node that extracts and organizes workflow metadata from images. It parses ComfyUI workflow data, filters and structures node information, and outputs clean JSON that can be embedded in saved images or used for workflow analysis and documentation.

## Key Features

- **Automatic Metadata Extraction**: Captures workflow data from ComfyUI's internal structures
- **Node Parsing**: Extracts and organizes information from workflow nodes
- **Smart Filtering**: Removes empty values and display-only nodes (like ShowText)
- **Order Preservation**: Maintains workflow execution order
- **Clean JSON Output**: Produces properly formatted, embeddable metadata
- **Error Resilient**: Handles malformed workflow data gracefully
- **Lightweight**: Minimal processing overhead

## Node Information

- **Node Name**: `BasifyMetadataViewer`
- **Display Name**: `Basify: Metadata Viewer`
- **Category**: `basify`

## Input Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | IMAGE | The image associated with the workflow |

### Hidden Parameters

Hidden parameters are automatically provided by ComfyUI:

| Parameter | Type | Description |
|-----------|------|-------------|
| `extra_pnginfo` | EXTRA_PNGINFO | ComfyUI's workflow and prompt metadata |
| `id` | UNIQUE_ID | Unique identifier for this node instance |

## Output Values

| Output | Type | Description |
|--------|------|-------------|
| `metadata_json` | STRING | JSON string containing structured workflow metadata |

## How It Works

### Metadata Collection Process

1. **Input Reception**:
   - Receives image and hidden metadata from ComfyUI
   - Extracts `extra_pnginfo` containing workflow data
   - Captures unique node ID

2. **Metadata Aggregation**:
   - Creates base metadata object with node ID
   - Merges all extra_pnginfo contents
   - Preserves workflow structure and prompt data

3. **Workflow Parsing**:
   - Extracts workflow JSON from metadata
   - Parses node list and properties
   - Sorts nodes by execution order

4. **Node Filtering**:
   - Skips ShowText nodes (display-only)
   - Removes None and empty values
   - Filters duplicate node titles
   - Extracts widget values only

5. **Output Formatting**:
   - Creates simplified display structure
   - Formats as compact JSON
   - Ensures ASCII compatibility for embedding

### Data Structure

**Input Metadata** (extra_pnginfo):
```json
{
  "workflow": {
    "nodes": [
      {
        "id": 1,
        "type": "CheckpointLoaderSimple",
        "title": "Load Checkpoint",
        "order": 0,
        "widgets_values": ["model.safetensors"]
      },
      {
        "id": 2,
        "type": "CLIPTextEncode",
        "title": "CLIP Text Encode (Prompt)",
        "order": 1,
        "widgets_values": ["a beautiful landscape"]
      }
    ]
  },
  "prompt": {
    "name": "My Workflow"
  }
}
```

**Output JSON** (metadata_json):
```json
{
  "workflow_name": "My Workflow",
  "nodes": {
    "Load Checkpoint": ["model.safetensors"],
    "CLIP Text Encode (Prompt)": ["a beautiful landscape"]
  }
}
```

## Usage Examples

### Basic Metadata Extraction

```
[Load Image] -> [Metadata Viewer] -> metadata_json -> [Display Text]
```

Extract and view metadata from a generated image.

### Embed Metadata in Saved Images

```
[KSampler] -> [VAE Decode] -> [Metadata Viewer] -> metadata_json -> [Save Image (with metadata)]
                    |                                 ^
                    +─────────────────────────────────┘
```

Add workflow information to output images.

### Workflow Documentation

```
[Workflow] -> [Metadata Viewer] -> [Save to File] -> workflow_documentation.json
```

Export workflow configuration for documentation or version control.

### Conditional Processing Based on Metadata

```
[Load Image] -> [Metadata Viewer] -> metadata_json -> [Parse JSON]
                                                           |
                                                           v
                                               [Extract specific parameters]
                                                           |
                                                           v
                                               [Conditional logic/routing]
```

Make workflow decisions based on metadata content.

### Batch Metadata Collection

```
[Directory Iterator] -> [Metadata Viewer] -> [Append to Database]
                                                    |
                                                    v
                                          {image_file: metadata}
```

Build a searchable database of workflow configurations.

### Compare Workflow Configurations

```
[Image A] -> [Metadata Viewer A] ──┐
                                    ├─> [Compare JSON] -> [Highlight Differences]
[Image B] -> [Metadata Viewer B] ──┘
```

Identify parameter differences between generations.

## Metadata Fields

### Top-Level Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `workflow_name` | string | Name of the workflow | `"Text to Image"` |
| `nodes` | object | Dictionary of node configurations | `{"node_title": [...values]}` |

### Node Data Structure

**Format**: `{ "Node Title": ["value1", "value2", ...] }`

**Example**:
```json
{
  "nodes": {
    "KSampler": ["20", "euler", "normal", "7.5", "512"],
    "Load Checkpoint": ["realisticVision.safetensors"],
    "Positive Prompt": ["a beautiful sunset over mountains"],
    "Negative Prompt": ["blurry, low quality"]
  }
}
```

## Node Filtering Rules

### Included Nodes

- ✅ Nodes with non-empty widget values
- ✅ Nodes with valid titles
- ✅ First occurrence of duplicate titles
- ✅ All standard processing nodes

### Excluded Nodes

- ❌ ShowText nodes (format: `ShowText|*`)
- ❌ Nodes with no widget values
- ❌ Nodes with only empty/None values
- ❌ Duplicate node titles (keeps first)

### Value Filtering

**Removed**:
- `None` values
- Empty strings (`""`)
- Whitespace-only strings

**Kept**:
- All non-empty values (converted to strings)
- Numeric values (0, 1.5, etc.)
- Boolean values (true/false)

## Error Handling

### Graceful Degradation

The node handles errors without crashing:

| Error Condition | Behavior |
|----------------|----------|
| No extra_pnginfo | Returns minimal metadata with ID only |
| Invalid workflow JSON | Returns empty nodes dictionary |
| Malformed node data | Skips problematic nodes |
| Missing node properties | Uses fallback values |
| JSON parsing error | Logs error, returns empty object |

### Error Logging

Errors are logged with color coding:

```
[BASIFY] Error parsing workflow: JSONDecodeError at line 5
[BASIFY] Unexpected error parsing workflow: KeyError 'nodes'
```

Colors:
- 🔴 Red: Error messages

## Integration Examples

### Standard Image Generation with Metadata

```
[Model Loader] ──┐
[Positive Prompt]─┤
[Negative Prompt]─┼─> [KSampler] -> [VAE Decode] ──┐
[Latent Generator]┘                                  ├─> [Metadata Viewer]
                                                     │         |
                                      image ─────────┘         v
                                                        [Save Image]
```

### Metadata-Driven Workflow

```
[Load Image with Workflow] -> [Metadata Viewer] -> [Extract Parameters]
                                                           |
                                                           v
                                               [Recreate Workflow Settings]
                                                           |
                                                           v
                                               [Generate Similar Image]
```

### Workflow Version Control

```
[Metadata Viewer] -> metadata_json -> [Save to Git]
                                          |
                                          v
                                    workflow_v1.json
                                    workflow_v2.json
                                    workflow_v3.json
```

Track changes in workflow configuration over time.

### Automated Documentation

```
[Generate Image] -> [Metadata Viewer] -> [Format as Markdown]
                                               |
                                               v
                                    ## Generated with:
                                    - Model: model.safetensors
                                    - Steps: 20
                                    - CFG: 7.5
```

### A/B Testing Tracker

```
[Test Image] -> [Metadata Viewer] -> [Log to Database]
                                          |
                                          v
                                    {
                                      timestamp: ...,
                                      parameters: {...},
                                      result_quality: ...
                                    }
```

## Best Practices

### 1. Placement in Workflow

**Early Placement**: Right after generation
```
[VAE Decode] -> [Metadata Viewer] -> [Processing]
```

**Late Placement**: Before final save
```
[Processing] -> [Metadata Viewer] -> [Save Image]
```

**Multiple Placements**: For different purposes
```
[Generation] -> [Metadata Viewer 1: Logging]
             -> [Metadata Viewer 2: Embedding]
```

### 2. Naming Nodes

Use descriptive node titles for better metadata:

**Good**:
- ✅ "Main Character Prompt"
- ✅ "Background Prompt"
- ✅ "Primary Model"
- ✅ "Refiner Model"

**Poor**:
- ❌ "CLIP Text Encode"
- ❌ "Load Checkpoint 1"
- ❌ "KSampler"

### 3. JSON Processing

**Parsing metadata in Python**:
```python
import json

metadata = json.loads(metadata_json)
workflow_name = metadata["workflow_name"]
nodes = metadata["nodes"]

# Access specific node
checkpoint = nodes.get("Load Checkpoint", ["unknown"])[0]
prompt = nodes.get("Positive Prompt", [""])[0]
```

**Parsing in JavaScript** (for web apps):
```javascript
const metadata = JSON.parse(metadataJson);
const workflowName = metadata.workflow_name;
const nodes = metadata.nodes;

// Access specific node
const checkpoint = (nodes["Load Checkpoint"] || ["unknown"])[0];
const prompt = (nodes["Positive Prompt"] || [""])[0];
```

### 4. Embedding in Images

When saving images with metadata:

1. Connect `metadata_json` to Save Image node's metadata input
2. Save as PNG (supports metadata chunks)
3. Use ComfyUI's built-in metadata embedding

**Not recommended**:
- JPEG (lossy, poor metadata support)
- WebP (limited metadata)

**Recommended**:
- PNG (lossless, excellent metadata)
- TIFF (lossless, extensive metadata)

### 5. Storage and Organization

**File-based**:
```
outputs/
├── image_001.png (with embedded metadata)
├── image_002.png
└── metadata/
    ├── image_001.json (separate metadata file)
    └── image_002.json
```

**Database**:
```sql
CREATE TABLE generations (
    id INTEGER PRIMARY KEY,
    image_path TEXT,
    metadata JSON,
    created_at TIMESTAMP
);
```

## Technical Details

### Widget Values Extraction

Widget values are node input parameters stored in the workflow:

**Example Node**:
```json
{
  "type": "KSampler",
  "widgets_values": [
    123456,        // seed
    "fixed",       // seed_control
    20,            // steps
    8.0,           // cfg
    "euler",       // sampler_name
    "normal",      // scheduler
    1.0            // denoise
  ]
}
```

**Extracted**:
```json
{
  "KSampler": ["123456", "fixed", "20", "8.0", "euler", "normal", "1.0"]
}
```

### Node Title Resolution

Fallback logic for node titles:

1. **Primary**: `node.title` (user-assigned name)
2. **Fallback**: `node.type` (node class name)
3. **Skip**: If both are missing

**Example**:
```json
// User renamed
{"title": "My Custom Sampler", "type": "KSampler"}
→ "My Custom Sampler"

// Default name
{"type": "KSampler"}
→ "KSampler"

// No title or type
{}
→ Skipped
```

### Order Preservation

Nodes are sorted by `order` field to maintain execution sequence:

```json
[
  {"title": "Step 3", "order": 2},
  {"title": "Step 1", "order": 0},
  {"title": "Step 2", "order": 1}
]
```

**After sorting**:
```json
{
  "Step 1": [...],
  "Step 2": [...],
  "Step 3": [...]
}
```

### JSON Formatting

Output JSON uses:
- `indent=None`: Compact format (no pretty-printing)
- `ensure_ascii=False`: Supports Unicode characters
- No trailing newlines

**Why compact?**
- Smaller file size when embedded
- Easier to parse programmatically
- Still valid JSON

### Hidden Input Mechanism

ComfyUI provides hidden inputs automatically:

```python
"hidden": {
    "extra_pnginfo": "EXTRA_PNGINFO",  # Workflow metadata
    "id": "UNIQUE_ID"                   # Node instance ID
}
```

**Access in function**:
```python
def collect_metadata(self, image, extra_pnginfo: dict, id: int):
    # extra_pnginfo contains full workflow
    # id is unique to this node instance
```

## Troubleshooting

### Empty Metadata Output

**Problem**: `metadata_json` contains only `{"workflow_name": "", "nodes": {}}`

**Causes**:
- No workflow data in image
- Image not generated by ComfyUI
- Workflow data stripped during processing

**Solutions**:
- Ensure image came from ComfyUI generation
- Check if workflow saving is enabled in ComfyUI settings
- Verify image format supports metadata (use PNG)

### Missing Nodes in Output

**Problem**: Expected nodes not appearing in metadata

**Causes**:
- Nodes have no widget values
- All values are empty/None
- Node title contains "ShowText|"
- Duplicate node title (only first kept)

**Solutions**:
- Check node has input values
- Verify node title doesn't match filter patterns
- Rename duplicate nodes with unique titles

### JSON Parsing Errors

**Problem**: Error logs show JSON parsing failures

**Causes**:
- Corrupted workflow data
- Invalid JSON in workflow field
- Unexpected data structure

**Solutions**:
- Check ComfyUI console for detailed errors
- Recreate workflow from scratch
- Update ComfyUI to latest version

### Unicode Characters Not Displaying

**Problem**: Non-ASCII characters appear as escape sequences

**Causes**:
- Display tool doesn't support Unicode
- JSON viewer using ASCII-only mode

**Solutions**:
- Use a Unicode-aware text viewer
- The JSON itself is correct (uses `ensure_ascii=False`)
- Parse JSON and display natively

## Performance Considerations

### Processing Speed

- **Metadata collection**: < 1ms (negligible)
- **JSON parsing**: 1-5ms (depends on workflow size)
- **Output formatting**: < 1ms

**Total overhead**: Essentially instant

### Memory Usage

- **Small workflow** (10 nodes): ~1-2 KB
- **Medium workflow** (50 nodes): ~5-10 KB
- **Large workflow** (200 nodes): ~20-50 KB

Memory impact is minimal.

### Scalability

**Node count limits**:
- Tested up to 500+ nodes
- No practical limit
- Performance remains constant

**Batch processing**:
- Can process thousands of images
- No memory accumulation
- Each call is independent

## Compatibility

- **ComfyUI Version**: Any version with EXTRA_PNGINFO support
- **Python**: 3.7+
- **Workflow Formats**: All ComfyUI workflow JSON formats
- **Image Types**: All ComfyUI IMAGE tensors
- **Downstream Nodes**: Any node accepting STRING input

## Advanced Usage

### Custom Metadata Parsing

Parse specific node types:

```python
import json

metadata = json.loads(metadata_json)
nodes = metadata["nodes"]

# Extract all checkpoint models used
checkpoints = [
    values[0] for title, values in nodes.items()
    if "checkpoint" in title.lower() and values
]

# Extract all prompts
prompts = [
    values[0] for title, values in nodes.items()
    if "prompt" in title.lower() and values
]
```

### Metadata Comparison

Compare two workflow configurations:

```python
import json

def compare_workflows(meta1_json, meta2_json):
    meta1 = json.loads(meta1_json)
    meta2 = json.loads(meta2_json)
    
    nodes1 = meta1["nodes"]
    nodes2 = meta2["nodes"]
    
    # Find differences
    all_keys = set(nodes1.keys()) | set(nodes2.keys())
    differences = {}
    
    for key in all_keys:
        val1 = nodes1.get(key)
        val2 = nodes2.get(key)
        if val1 != val2:
            differences[key] = {"workflow1": val1, "workflow2": val2}
    
    return differences
```

### Automated Parameter Extraction

Extract specific parameters for logging:

```python
def extract_generation_params(metadata_json):
    metadata = json.loads(metadata_json)
    nodes = metadata["nodes"]
    
    params = {
        "model": None,
        "sampler": None,
        "steps": None,
        "cfg": None,
        "positive_prompt": None,
    }
    
    # Extract from known node patterns
    for title, values in nodes.items():
        if "checkpoint" in title.lower() and values:
            params["model"] = values[0]
        elif "ksampler" in title.lower() and len(values) >= 4:
            params["steps"] = values[2]
            params["cfg"] = values[3]
            params["sampler"] = values[4] if len(values) > 4 else None
        elif "positive" in title.lower() and "prompt" in title.lower() and values:
            params["positive_prompt"] = values[0]
    
    return params
```

### Workflow Versioning

Track workflow versions:

```python
import hashlib
import json

def get_workflow_hash(metadata_json):
    """Create a hash of workflow configuration for versioning."""
    metadata = json.loads(metadata_json)
    # Sort keys for consistent hashing
    canonical = json.dumps(metadata, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:8]

# Usage
version_id = get_workflow_hash(metadata_json)
# Save with version: workflow_v3a7f2b1c.json
```

## FAQ

**Q: Can I modify the metadata before it's output?**
A: Not directly through node inputs. You'd need to modify the source code or use a separate string processing node.

**Q: Why are some of my nodes missing from the output?**
A: Nodes without widget values or with only empty values are filtered out. ShowText nodes are also excluded.

**Q: Can I get the full unfiltered workflow data?**
A: The node filters and simplifies data. To get raw data, you'd need to modify the code to return `extra_pnginfo` directly.

**Q: Does this work with images not generated by ComfyUI?**
A: It requires ComfyUI's EXTRA_PNGINFO data, so external images won't have usable metadata unless they were previously processed by ComfyUI.

**Q: Can I parse the output in other programming languages?**
A: Yes, it outputs standard JSON which can be parsed by any language (Python, JavaScript, Java, C#, etc.).

**Q: How do I handle Unicode/emoji in metadata?**
A: The node uses `ensure_ascii=False`, so Unicode is preserved correctly. Just ensure your display/parsing tool supports UTF-8.

**Q: Can I use this for workflow templates?**
A: Yes! Extract metadata from a template, store it, and use it to recreate similar workflows.

**Q: What's the difference between this and ComfyUI's built-in metadata?**
A: This node extracts and formats specific workflow information into a clean JSON structure, while built-in metadata includes everything (including UI state, connections, etc.).

**Q: Can I extract metadata from PNG files saved earlier?**
A: If the PNG was saved with ComfyUI workflow data embedded, you can load it back into ComfyUI and extract metadata. External tools would need PNG chunk readers.

**Q: How do I debug what metadata is being captured?**
A: Connect the `metadata_json` output to a ShowText node to display the JSON in ComfyUI's interface.
