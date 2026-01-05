# Display Anything as Text Node

## Overview

The **Basify: Display Anything as Text** node is a universal debugging and inspection tool for ComfyUI workflows. It accepts any type of input and displays it as human-readable text in a readonly textarea widget. The node also passes through the original value unchanged, making it perfect for inline debugging without disrupting your workflow.

## Features

- **Universal Input**: Accepts any type of value (`*` wildcard input)
- **Intelligent Conversion**: Automatically converts values to appropriate text representations
- **Passthrough Design**: Outputs the original value unchanged for workflow continuity
- **Comprehensive Display**: Shows detailed information for complex types
- **Safe Handling**: Gracefully handles errors and unconvertible values
- **Size Management**: Truncates extremely large outputs to prevent workflow bloat

## Use Cases

1. **Debugging**: Insert between nodes to inspect intermediate values
2. **Data Exploration**: Examine the structure and content of complex data types
3. **Tensor Inspection**: View detailed statistics about image tensors
4. **Configuration Review**: Display JSON/dict configurations in readable format
5. **Type Checking**: Verify the type and content of node outputs

## Input/Output

### Inputs

- **value** (`*`): Any value to display as text
  - Primitive types: `str`, `int`, `float`, `bool`
  - Collections: `list`, `tuple`, `dict`, `set`
  - Tensors: PyTorch tensors, NumPy arrays
  - Objects: Custom classes and other Python objects

### Outputs

- **value** (`*`): The original input value, passed through unchanged

## Supported Types & Display Formats

### Primitive Types
```
Input: 42
Display: 42

Input: "Hello World"
Display: Hello World

Input: True
Display: True
```

### Collections
```python
Input: {"name": "test", "count": 5}
Display:
{
  "name": "test",
  "count": 5
}

Input: [1, 2, 3, 4, 5]
Display:
[
  1,
  2,
  3,
  4,
  5
]
```

### PyTorch Tensors
```
Input: torch.randn(3, 512, 512)
Display:
PyTorch Tensor
  Shape: (3, 512, 512)
  Dtype: torch.float32
  Device: cpu
  Requires grad: False
  Min: -3.924561
  Max: 4.127832
  Mean: 0.001234
  Std: 1.003456
```

### NumPy Arrays
```
Input: np.array([[1, 2], [3, 4]])
Display:
NumPy Array
  Shape: (2, 2)
  Dtype: int64
  Size: 4 elements
  Min: 1.000000
  Max: 4.000000
  Mean: 2.500000
  Std: 1.118034

Values:
[[1 2]
 [3 4]]
```

### Unknown/Complex Objects
```
Input: <custom object>
Display:
Type: MyCustomClass

Public attributes: method1, method2, property1, property2
```

## Size Limits

To prevent workflow file bloat, the node limits display to **50,000 characters**. Larger outputs are truncated with a message indicating how many characters were omitted:

```
[... content ...]

... [truncated 25,432 characters]
```

This limit can be adjusted in the Python source if needed (`MAX_DISPLAY_LENGTH`).

## Implementation Details

### Architecture

The node follows the standard ComfyUI custom node pattern with two components:

1. **Python Backend** ([py/display_anything.py](../display_anything.py))
   - Receives input value
   - Converts to text representation
   - Returns both UI data and passthrough value

2. **JavaScript Frontend** ([js/display_anything.js](../display_anything.js))
   - Creates readonly textarea widget
   - Updates display when node executes
   - Handles workflow save/load

### Conversion Logic

The node uses a priority-based conversion strategy:

1. `None` → `"None"`
2. Primitives (`str`, `int`, `float`, `bool`) → `str(value)`
3. `bytes` → UTF-8 decode or hex representation
4. PyTorch Tensors → Detailed statistics and shape info
5. NumPy Arrays → Detailed statistics and shape info
6. Dictionaries → JSON formatted with indentation
7. Lists/Tuples → JSON formatted with indentation
8. Sets → List representation
9. Other Objects → Safe `repr()` or attribute listing

### Error Handling

If conversion fails at any step, the node:
- Logs the error
- Displays error information including exception type and value type
- Still passes through the original value
- Does not crash the workflow

## Workflow Integration

### Basic Usage
```
[Any Node] → [Display Anything as Text] → [Next Node]
```
The display node shows the value but doesn't interrupt the data flow.

### Multiple Inspection Points
```
[LoadImage] → [Display #1] → [Preprocess] → [Display #2] → [Model]
```
Insert multiple display nodes to track data transformations through your workflow.

### Branching
```
[Generator] → [Display Anything as Text] ┬→ [Path A]
                                         └→ [Path B]
```
The passthrough design allows branching without duplicating nodes.

## Performance Considerations

- **Memory**: Text conversion creates temporary strings but releases them after display
- **Workflow Size**: Large tensor statistics are concise; truncation prevents bloat
- **Execution**: Minimal overhead, suitable for production workflows
- **CPU Usage**: Tensor statistics require CPU calculation but only on execution

## Customization

To modify behavior, edit the Python source:

```python
# Change maximum display length
MAX_DISPLAY_LENGTH = 100000  # 100k characters

# Adjust tensor sample sizes
if tensor.numel() <= 1000:  # Show more/fewer values
    lines.append(f"\nFirst 100 values:\n{cpu_tensor.flatten()[:100]}")
```

## Comparison with Other Nodes

| Feature | Display Anything | ShowText | Metadata Viewer |
|---------|-----------------|----------|-----------------|
| Input Type | Any (`*`) | String only | Image only |
| Passthrough | ✓ Yes | ✗ No | ✓ Yes |
| Tensor Stats | ✓ Detailed | ✗ No | ✗ No |
| JSON Formatting | ✓ Auto | Manual | ✓ Auto |
| Use Case | Universal debug | Text display | Workflow metadata |

## Troubleshooting

**Q: Widget is empty even though node executed**
- Check the JavaScript console for errors
- Verify the input is connected
- Try a simple input like a string or integer first

**Q: Display shows "Error converting value to text"**
- The object couldn't be converted safely
- Check logs for detailed error information
- The original value still passes through

**Q: Workflow file size increased significantly**
- Large text displays are saved with the workflow
- Consider using fewer display nodes or reducing `MAX_DISPLAY_LENGTH`
- Display nodes can be disabled without removing them

**Q: Tensor statistics not showing**
- Ensure PyTorch is installed and accessible
- Check that the input is actually a tensor
- Verify tensor is not empty or malformed

## Examples

### Example 1: Debugging Image Processing
```
[LoadImage] → [Display: Check Input]
    ↓
[Resize] → [Display: After Resize]
    ↓
[Normalize] → [Display: After Normalize]
    ↓
[Model]
```

### Example 2: Inspecting Configuration
```
[LoadJSON] → [Display Anything as Text]
    ↓
[ConfigParser]
```
View the full JSON structure before parsing.

### Example 3: Type Verification
```
[CustomNode] → [Display Anything as Text] → [RequiresSpecificType]
```
Verify that CustomNode outputs the expected type.

## Version History

- **v1.0.0** (2026-01-05): Initial release
  - Universal input support
  - Passthrough design
  - Comprehensive type conversion
  - Tensor statistics
  - Automatic truncation

## License

Same as parent Basify project.

## Contributing

To enhance the node:
1. Add new type handlers in `_convert_to_text()`
2. Improve statistics for specific tensor types
3. Add configuration options via input parameters
4. Optimize large object handling
