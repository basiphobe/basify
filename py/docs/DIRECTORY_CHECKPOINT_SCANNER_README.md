# Directory Checkpoint Scanner

## Overview

The **Directory Checkpoint Scanner** is a ComfyUI custom node that scans a directory (including subdirectories) for checkpoint model files and provides an easy way to select and load them. It features symbolic link support, automatic deduplication, and remembers your last selection per directory for improved workflow efficiency.

## Key Features

- **Recursive Scanning**: Automatically scans subdirectories for checkpoint files
- **Symbolic Link Support**: Follows symbolic links and shows link targets
- **Deduplication**: Prevents duplicate entries when the same model is linked multiple times
- **Selection Memory**: Remembers the last selected checkpoint for each directory
- **Multiple Formats**: Supports various checkpoint file formats
- **Subdirectory Display**: Shows relative paths including subdirectory structure
- **Error Resilience**: Gracefully handles permission errors and missing files

## Node Information

- **Node Name**: `DirectoryCheckpointScanner`
- **Display Name**: `Basify: Directory Checkpoint Scanner`
- **Category**: `loaders`

## Input Parameters

### Required Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `directory_path` | STRING | ComfyUI checkpoints folder | Directory to scan for checkpoint models |
| `selected_checkpoint` | STRING | Last selection | The checkpoint file to load (dropdown populated from scan) |

**Note**: The `directory_path` defaults to ComfyUI's configured checkpoints directory (`folder_paths.get_folder_paths("checkpoints")[0]`).

## Output Values

| Output | Type | Description |
|--------|------|-------------|
| `model` | MODEL | The loaded model from the checkpoint |
| `clip` | CLIP | The CLIP model from the checkpoint |
| `vae` | VAE | The VAE model from the checkpoint |
| `full_path` | STRING | Full absolute path to the loaded checkpoint file |

## Supported Checkpoint Formats

- `.ckpt` - Original Stable Diffusion checkpoint format
- `.safetensors` - SafeTensors format (recommended)
- `.pt` - PyTorch model file
- `.pth` - PyTorch model file (alternative extension)

## How It Works

### Directory Scanning

1. **Recursive Walk**: Uses `os.walk()` with `followlinks=True` to traverse directory tree
2. **Extension Matching**: Identifies files with supported checkpoint extensions
3. **Link Resolution**: Resolves symbolic links to their real paths
4. **Deduplication**: Tracks real paths to prevent duplicate entries
5. **Path Display**: Shows relative paths from the base directory

### Symbolic Link Handling

When a symbolic link is detected, the display name shows:
```
model_name.safetensors → actual/path/to/model.safetensors
```

This helps you identify links and understand the actual file location.

### Selection Memory

The node maintains a JSON file (`.checkpoint_selections.json`) that stores the last selected checkpoint for each directory:

```json
{
  "/path/to/checkpoints": "subfolder/model.safetensors",
  "/another/path": "another_model.ckpt"
}
```

This ensures that when you reopen a workflow or switch directories, your previous selection is automatically restored.

### Checkpoint Loading

Uses ComfyUI's `comfy.sd.load_checkpoint_guess_config()` to:
- Automatically detect checkpoint configuration
- Load MODEL, CLIP, and VAE components
- Handle various checkpoint formats and structures

## Usage Examples

### Basic Usage

1. Add the **Basify: Directory Checkpoint Scanner** node to your workflow
2. Set `directory_path` to your models folder (or use the default)
3. Select a checkpoint from the dropdown
4. Connect outputs to your workflow:
   - `model` → KSampler or other model nodes
   - `clip` → CLIP Text Encode nodes
   - `vae` → VAE Decode nodes

### Organizing Models with Subdirectories

```
checkpoints/
├── sd15/
│   ├── realistic.safetensors
│   └── artistic.ckpt
├── sdxl/
│   ├── base.safetensors
│   └── refiner.safetensors
└── anime/
    └── animagine.safetensors
```

The dropdown will show:
- `anime/animagine.safetensors`
- `sd15/artistic.ckpt`
- `sd15/realistic.safetensors`
- `sdxl/base.safetensors`
- `sdxl/refiner.safetensors`

### Using Symbolic Links

Create symbolic links to organize models without duplicating files:

```bash
# Create a symlink to a model in a different location
ln -s /storage/models/my_model.safetensors /checkpoints/favorites/my_model.safetensors
```

The scanner will:
- Follow the link and load the actual model
- Show the link relationship in the dropdown
- Deduplicate if the same model is linked multiple times

### Switching Between Checkpoint Directories

You can switch directories dynamically:
1. Change the `directory_path` value
2. The dropdown refreshes with checkpoints from the new directory
3. The last selection for that directory is automatically restored

## Display Messages

| Message | Meaning |
|---------|---------|
| `"No directory path provided"` | The directory_path parameter is empty |
| `"Directory does not exist"` | The specified directory doesn't exist |
| `"Path is not a directory"` | The path points to a file, not a directory |
| `"No checkpoints found"` | Directory exists but contains no checkpoint files |
| `"Permission denied: <details>"` | Insufficient permissions to read the directory |
| `"Error scanning directory: <details>"` | An error occurred during scanning |

## Error Handling

The node handles various error conditions gracefully:

### Directory Errors
- **Missing Directory**: Returns empty results with error message
- **Permission Denied**: Logs error and shows message in dropdown
- **Not a Directory**: Shows error message if path is a file

### File Errors
- **Broken Symlinks**: Skips links that point to non-existent files
- **Inaccessible Files**: Logs warning and continues scanning
- **Invalid Checkpoints**: Returns None values if loading fails

### State Management
- **Corrupted Selection File**: Falls back to defaults if `.checkpoint_selections.json` is corrupted
- **Missing Selection**: Uses empty string if no previous selection exists

## Best Practices

### 1. Directory Organization
Organize checkpoints in subdirectories by:
- Model type (SD 1.5, SDXL, etc.)
- Style (realistic, anime, artistic)
- Purpose (base models, fine-tunes, experiments)

### 2. Use Symbolic Links Wisely
- Link frequently-used models to a "favorites" folder
- Create workflow-specific directories with links to relevant models
- Keep original models in a central location

### 3. Naming Conventions
Use descriptive filenames:
- ✅ `sdxl_realistic_photoreal_v2.safetensors`
- ✅ `sd15_anime_animagine_xl.safetensors`
- ❌ `model1.ckpt`
- ❌ `untitled.safetensors`

### 4. Checkpoint Format
Prefer `.safetensors` format:
- Faster loading
- More secure
- Better metadata support

### 5. Performance Considerations
- Large directories with many subdirectories may take longer to scan
- The scan happens each time the node is refreshed
- Consider organizing into smaller subdirectories for faster scanning

### 6. Network and Cloud Storage
The scanner works with network-mounted directories and cloud storage, but:
- Ensure stable network connection
- Be aware of increased latency
- Consider caching frequently-used models locally

## Troubleshooting

### Checkpoints Not Appearing

**Problem**: Expected checkpoints don't show in the dropdown

**Solutions**:
- Verify the directory path is correct
- Check file extensions match supported formats
- Ensure you have read permissions
- Look for error messages in the ComfyUI console
- Try refreshing the node

### "Permission Denied" Error

**Problem**: Cannot access directory

**Solutions**:
- Check file system permissions
- Run ComfyUI with appropriate user permissions
- Verify the directory is not locked by another process
- On Linux/Mac: `chmod +r` the directory

### Symbolic Links Not Working

**Problem**: Symlinks aren't being followed

**Solutions**:
- Ensure the link target exists
- Check that the target has read permissions
- Verify the link isn't broken: `ls -l /path/to/link`
- On Windows, ensure you have symlink creation privileges

### Selection Not Remembered

**Problem**: Last selection isn't restored

**Solutions**:
- Check write permissions in the `py/` directory
- Verify `.checkpoint_selections.json` exists and is valid JSON
- Delete the file to reset all selections
- Check ComfyUI console for save errors

### Duplicate Entries

**Problem**: Same model appears multiple times

**Solutions**:
- This should not happen due to deduplication
- If it does, check for files with different names pointing to different copies
- Symlinks to the same file are automatically deduplicated

### Loading Fails

**Problem**: Checkpoint selected but nothing loads

**Solutions**:
- Check ComfyUI console for detailed error messages
- Verify the checkpoint file isn't corrupted
- Ensure the file format is compatible with your ComfyUI version
- Try loading the checkpoint with ComfyUI's standard loader as a test

## Integration Examples

### Basic Model Loading
```
[Directory Checkpoint Scanner] -> model -> [KSampler]
                                -> clip -> [CLIP Text Encode (Positive)]
                                         -> [CLIP Text Encode (Negative)]
                                -> vae -> [VAE Decode]
```

### Multiple Checkpoints
```
[Directory Checkpoint Scanner (Base)] -> [Workflow Part 1]
[Directory Checkpoint Scanner (Refiner)] -> [Workflow Part 2]
```

### Path-Based Automation
```
[Directory Checkpoint Scanner] -> full_path -> [String Processing]
                                                      |
                                                      v
                                            [Conditional Logic Based on Path]
```

## Technical Details

### Deduplication Algorithm

1. For each file, resolve to real path using `os.path.realpath()`
2. Check if real path exists in `seen_real_paths` set
3. If seen, skip; if new, add to set and to results
4. This ensures each unique file appears once, regardless of symlinks

### Selection Storage

**File Location**: `py/.checkpoint_selections.json`

**Format**:
```json
{
  "/absolute/path/to/directory": "relative/path/to/checkpoint.safetensors"
}
```

**Key**: Absolute path to directory (normalized)
**Value**: Relative path to checkpoint (as shown in dropdown)

### Lazy Module Loading

The node uses lazy imports for ComfyUI modules:
```python
def get_comfy_modules():
    import comfy.sd
    return comfy.sd
```

This prevents import errors during package initialization and ensures modules are loaded only when needed.

### Path Handling

- **Input**: Relative path from `directory_path`
- **Processing**: Combined with `directory_path` to create full path
- **Symlink Resolution**: Resolved to actual file path
- **Output**: Absolute path to actual checkpoint file

### Checkpoint Loading Configuration

Uses `load_checkpoint_guess_config()` which:
- Automatically detects model architecture
- Handles various checkpoint formats
- Extracts MODEL, CLIP, and VAE components
- Uses ComfyUI's embedding directory for textual inversions

## Compatibility

- **ComfyUI**: Requires ComfyUI framework
- **Python**: Python 3.8+
- **OS**: Windows, Linux, macOS
- **File Systems**: Supports any file system with symbolic link capability

## Performance Optimization

### Scanning Speed
- Scanning time increases with:
  - Number of subdirectories
  - Total file count
  - Network latency (for remote storage)

### Memory Usage
- Minimal memory footprint
- Only stores file paths, not loaded models
- Selection file is small JSON (typically < 1 KB)

### Caching
- No built-in caching of directory scans
- Each refresh re-scans the directory
- Model loading uses ComfyUI's internal caching

## Security Considerations

- **Symbolic Link Traversal**: The scanner follows symlinks, which could potentially access unintended locations if links are maliciously crafted
- **Path Validation**: Limited validation of paths - ensure directory sources are trusted
- **SafeTensors**: Prefer `.safetensors` format for better security against pickle exploits in `.ckpt` files

## Advanced Usage

### Custom Directory Structures

For complex setups with multiple model repositories:

```
/models/
├── stable-diffusion/
│   └── sd15/ -> /storage/models/sd15/
├── stable-diffusion-xl/
│   └── sdxl/ -> /storage/models/sdxl/
└── custom/
    ├── personal/
    └── experimental/
```

### Scripted Model Management

Use the `full_path` output for:
- Logging which models are used in generations
- Automated model selection based on prompts
- Building model usage statistics

### Multi-Model Workflows

Chain multiple scanners for complex workflows:
- Base model scanner
- Refiner model scanner
- Upscaler model scanner

Each maintains independent selection memory.

## Comparison with Standard Checkpoint Loader

| Feature | Directory Checkpoint Scanner | Standard Loader |
|---------|------------------------------|-----------------|
| Subdirectories | ✅ Automatic | ❌ Flat list |
| Symbolic Links | ✅ Full support | ⚠️ Limited |
| Deduplication | ✅ Automatic | ❌ Shows duplicates |
| Selection Memory | ✅ Per directory | ❌ None |
| Custom Directories | ✅ Any directory | ⚠️ Configured paths only |
| Organization | ✅ Shows structure | ❌ Flat alphabetical |

## Future Enhancements

Potential features for future versions:
- Thumbnail previews
- Model metadata display (training info, trigger words)
- Favorite checkpoints marking
- Search/filter functionality
- Recently-used list
- Model grouping/tagging
