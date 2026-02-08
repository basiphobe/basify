# Lazy Conditional Switch

## Overview

The **Lazy Conditional Switch** node implements true lazy conditional branching in ComfyUI workflows. It evaluates only the selected branch based on a boolean condition, completely avoiding execution of the unselected branch.

This is critical for workflows where one branch may trigger expensive GPU operations (such as GroundingDINO + SAM segmentation) that should be bypassed when not needed.

## Key Features

- **True Lazy Evaluation**: Only the selected input is evaluated; the unselected input is never computed
- **Prevents Upstream Execution**: Nodes feeding the unselected input are not executed at all
- **Type Agnostic**: Works with any ComfyUI data type (ANY sockets)
- **Performance Critical**: Essential for avoiding OOM errors and unnecessary GPU operations

## Use Case

Perfect for conditional workflows like:
- Bypassing segmentation when no objects are detected
- Skipping upscaling when image is already large enough
- Avoiding model inference when cache hit occurs
- Any scenario where one branch is computationally expensive and should only run when needed

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `condition` | BOOLEAN | Yes | Determines which branch to evaluate and return (accepts bool, int, or float) |
| `true_value` | ANY | Yes (lazy) | Value to evaluate and return when condition is True |
| `false_value` | ANY | Yes (lazy) | Value to evaluate and return when condition is False |

**Note**: Both branch inputs are marked as `required` with `lazy: True` to ensure proper lazy evaluation within ComfyUI's execution contract. They are not evaluated until requested by `check_lazy_status`.

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `value` | ANY | The value from the selected branch (matches the type of the evaluated input) |

## How It Works

1. **Condition Evaluation**: The `condition` input is always evaluated first
2. **Lazy Selection**: Based on the condition value:
   - If `True`: Only `true_value` is evaluated; `false_value` remains untouched
   - If `False`: Only `false_value` is evaluated; `true_value` remains untouched
3. **Output**: The selected value is returned with its original type

## Important Notes

### Lazy Evaluation Mechanism

The node uses ComfyUI's `check_lazy_status` method to tell the execution engine which inputs to evaluate **before** they are computed. This means:

- Unselected inputs are truly never evaluated
- Upstream nodes feeding unselected inputs don't execute
- No GPU memory is allocated for unselected branches
- No time is wasted on unnecessary computations

### Difference from Regular Switch/Mux

A regular switch/mux node would:
1. Evaluate BOTH inputs first
2. Then select which one to output

This lazy switch:
1. Checks the condition
2. Evaluates ONLY the selected input
3. Returns that value

This is the difference between "selecting after computation" and "computing only what's selected".

## Example Workflow

```
[GroundingDINO Detect] → has_detections (BOOLEAN)
                       ↓
[SAM Segmentation] → true_value  ─┐
                                  │
[Empty Mask] → false_value  ──────┼─→ [Lazy Conditional Switch] → output
                                  │
        has_detections ───────────┘
```

In this example:
- If `has_detections` is False, SAM is never executed (saves GPU memory and time)
- If `has_detections` is True, SAM executes and Empty Mask is skipped

## Technical Details

### Implementation

The node implements two key methods:

1. **`check_lazy_status(condition, true_value, false_value)`**:
   - Called by ComfyUI before evaluation
   - Checks if selected input is `None` (unevaluated)
   - Returns `["true_value"]` or `["false_value"]` based on condition
   - Converts condition to bool (handles int/float from comparison nodes)
   - Prevents evaluation of unselected input

2. **`switch(condition, true_value, false_value)`**:
   - Called after lazy evaluation
   - Validates selected value is not None (fails fast if lazy gate failed)
   - Converts condition to bool (defensive programming)
   - Returns the selected value

### Defensive Features

- **Type coercion**: Converts condition to `bool()` to handle comparison nodes that output 0/1
- **Failsafe validation**: Raises `RuntimeError` if selected value is still `None`, catching lazy evaluation failures immediately
- **Required lazy inputs**: Both branches are required inputs (with `lazy: True`) to ensure proper evaluation contract

### Type Handling

The node uses `IO.ANY` for both inputs and output, allowing it to work with:
- Images (IMAGE)
- Latents (LATENT)
- Masks (MASK)
- Text (STRING)
- Numbers (INT, FLOAT)
- Models (MODEL)
- Any custom types

The output type dynamically matches whichever input was selected.

## Logging

The node logs debug messages showing:
- Which branch is being evaluated
- The type of value being returned

Enable debug logging to see: `[BASIFY Lazy Conditional Switch] Condition is True, evaluating true_value`

## Category

`basify`
