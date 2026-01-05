# Conditional Validator Node

## Overview

The **Basify: Conditional Validator** node is a workflow control tool that validates a boolean condition before passing through a value. If the condition is `True`, the value passes through unchanged. If the condition is `False`, the node raises an error and stops workflow execution.

This is useful for halting workflows when validation fails or when there's nothing more to process.

## Features

- **Boolean Validation**: Checks a condition before allowing workflow continuation
- **Error on Failure**: Stops the entire workflow if validation fails
- **Passthrough Design**: Outputs the original value unchanged when validation succeeds
- **Custom Error Messages**: Optional user-defined error message for debugging
- **Universal Input**: Accepts any type of value to pass through
- **Workflow Safety**: Prevents further processing when conditions aren't met

## Use Cases

1. **Validation Gates**: Stop execution if required conditions aren't met
2. **Empty Queue Detection**: Halt when there are no more items to process
3. **Resource Checks**: Verify resources exist before attempting to use them
4. **State Validation**: Ensure workflow state is valid before proceeding
5. **Batch Processing**: Stop when batch processing is complete

## Input/Output

### Inputs

- **condition** (`BOOLEAN`, required): 
  - Boolean condition to validate
  - `True`: allows value to pass through
  - `False`: raises error and stops workflow
  - Default: `True`

- **value** (`*`, required):
  - Any value to pass through when condition is True
  - Can be any type: images, latents, strings, numbers, etc.

- **error_message** (`STRING`, optional):
  - Custom error message displayed when condition is False
  - Multiline text supported
  - Default: `"Validation failed: condition is False"`

### Outputs

- **value** (`*`): The original input value, passed through unchanged (only when condition is True)

## Behavior

### When Condition is True
```
Input:
  condition: True
  value: <any_value>

Output:
  value: <any_value> (passed through)
  
Workflow: Continues normally
```

### When Condition is False
```
Input:
  condition: False
  value: <any_value>
  error_message: "No more items to process"

Output:
  ERROR: No more items to process
  
Workflow: Stops execution immediately
```

## Examples

### Example 1: Stop When Queue is Empty

```
[Queue Size Checker] → condition
[Next Item Getter] → value
[Custom Message] → error_message: "Queue is empty, stopping workflow"

→ [Basify: Conditional Validator]
  ↓ (if True)
[Process Item] → (continues workflow)
```

If queue size is 0 (False), workflow stops with message "Queue is empty, stopping workflow".
If queue has items (True), the next item passes through for processing.

### Example 2: Resource Validation

```
[Check File Exists] → condition
[File Path] → value
[Error Message] → "Required file not found"

→ [Basify: Conditional Validator]
  ↓ (if True)
[Load Image] → (continues with file)
```

### Example 3: Chain Multiple Validators

```
[Validator 1: Check Input Valid] → value
  ↓
[Validator 2: Check Output Dir Exists] → value
  ↓
[Validator 3: Check Disk Space] → value
  ↓
[Process] (only runs if all validations pass)
```

## Error Handling

When the condition is `False`:
- A `ValueError` is raised with the provided error message
- Workflow execution stops immediately
- The error appears in ComfyUI's console/log
- Downstream nodes do not execute

The error log will show:
```
ERROR [BASIFY Conditional Validator] <your_custom_message>
```

## Workflow Design Tips

1. **Place Early**: Put validators early in the workflow to fail fast
2. **Descriptive Messages**: Use clear error messages for easier debugging
3. **Multiple Validators**: Chain validators for complex validation logic
4. **Default Values**: Use default error message for simple "must be true" checks
5. **Condition Sources**: Connect to boolean outputs from comparison nodes, file check nodes, etc.

## Technical Details

- **Category**: `basify`
- **Function**: `validate_and_pass`
- **Output Node**: No (but stops execution on failure)
- **Logging**: Logs both successes (debug) and failures (error)

## Common Patterns

### Stop on Completion
```python
# Check if batch processing is complete
[Batch Counter] → is_complete → condition
[Current Batch] → value
→ [Conditional Validator with message: "Batch processing complete"]
```

### Require User Input
```python
# Don't run without required input
[Input Field != ""] → condition
[Input Field] → value
→ [Conditional Validator with message: "Input field is required"]
```

### File/Directory Guards
```python
# Only process if file exists
[os.path.exists(file)] → condition
[File Path] → value
→ [Conditional Validator with message: "Input file not found"]
```

## Notes

- The node uses Python's truthy evaluation, but expects actual boolean values
- Error messages support multiline text for detailed failure descriptions
- The value input accepts any type and preserves it exactly when passing through
- Execution stops completely; no downstream nodes will run after a failed validation
