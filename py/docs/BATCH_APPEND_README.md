# Batch Append Node

## Overview

The **Basify: Batch Append** node provides flexible batch accumulation and appending functionality for ComfyUI workflows. It can append items to existing batches or maintain an internal accumulating collection, making it essential for building dynamic batches, processing sequences, and accumulating results over multiple workflow iterations.

## Features

- **Flexible Input Handling**: Works with any data type (images, latents, tensors, lists, etc.)
- **Multiple Batch Types**: Handles lists, torch tensors, latent dicts, and custom collections
- **Internal Accumulation**: Maintains persistent collection when no batch input is connected
- **Smart Type Detection**: Automatically detects item type and creates appropriate collection
- **Type Change Detection**: Resets internal collection when item type changes
- **Batch Concatenation**: Intelligently concatenates tensors along batch dimension
- **Stateful Operation**: Remembers accumulated items across executions

## Use Cases

1. **Dynamic Batch Building**: Accumulate multiple items into a batch over successive iterations
2. **Image Collection**: Build image batches from individual generated images
3. **Latent Accumulation**: Collect latent tensors for batch processing
4. **List Building**: Construct lists of any type of items
5. **Queue Processing**: Accumulate results from iterative workflows
6. **Conditional Accumulation**: Build batches based on workflow conditions

## Input/Output

### Inputs

- **item** (`*`, required):
  - Any item to append to the batch or internal collection
  - Can be any type: IMAGE, LATENT, MASK, STRING, INT, etc.
  - The collection type will match the item type

- **batch** (`*`, optional):
  - Optional batch to append to
  - If **not connected**: Uses internal accumulating collection
  - If **connected but None**: Creates new single-item collection
  - If **connected with value**: Appends item to provided batch

### Outputs

- **batch** (`*`): 
  - The batch with the item appended
  - Type matches the input item type
  - Format depends on the collection type (list, tensor, dict, etc.)

## Behavior Modes

### Mode 1: Internal Accumulation (batch input not connected)

When the `batch` input is **not connected**, the node maintains an internal collection that persists across executions:

```
First execution:
  item: <value1>
  batch: [not connected]
  → Output: [value1]

Second execution:
  item: <value2>
  batch: [not connected]
  → Output: [value1, value2]

Third execution:
  item: <value3>
  batch: [not connected]
  → Output: [value1, value2, value3]
```

**Internal collection resets when:**
- Item type changes (e.g., from IMAGE to STRING)
- Batch input becomes connected
- Workflow is reset

### Mode 2: New Collection from None (batch connected, value is None)

When the `batch` input is **connected but has a None value**, the node creates a fresh collection:

```
Execution:
  item: <value>
  batch: None (connected)
  → Output: [value]  (single-item collection, no accumulation)
```

### Mode 3: Append to External Batch (batch connected with value)

When the `batch` input is **connected with a value**, the node appends to that batch:

```
Execution:
  item: <new_value>
  batch: [value1, value2]
  → Output: [value1, value2, new_value]
```

This mode **resets the internal collection** since an external batch takes priority.

## Collection Type Handling

### Lists and Tuples
- Converts to list and appends item
- Example: `[1, 2, 3]` + `4` → `[1, 2, 3, 4]`

### Torch Tensors
- Concatenates along batch dimension (dim=0)
- Automatically adds batch dimension if needed
- Example: `[B=2, C, H, W]` + `[C, H, W]` → `[B=3, C, H, W]`

### Latent Dicts (IMAGE/LATENT format)
- Recognizes dicts with `'samples'` key
- Concatenates sample tensors
- Example: `{'samples': [2, 4, 64, 64]}` + `{'samples': [1, 4, 64, 64]}` → `{'samples': [3, 4, 64, 64]}`

### Mixed Types
- If types don't match, converts to list
- Example: Tensor + String → `[tensor, "string"]`

## Type Change Detection

The node tracks the type of items being accumulated. When the item type changes, the internal collection is automatically reset:

```
Execution 1:
  item: <image1> (IMAGE type)
  → Internal: [image1]

Execution 2:
  item: <image2> (IMAGE type)
  → Internal: [image1, image2]

Execution 3:
  item: "text" (STRING type)
  → Type changed! Internal collection reset
  → Internal: ["text"]
```

This prevents incompatible types from being mixed in the same collection.

## Examples

### Example 1: Building an Image Batch

**Workflow**: Generate multiple images and accumulate them into a batch

```
Setup:
- Generate image nodes feeding into Batch Append (item input)
- batch input: not connected
- Run workflow multiple times

Result:
- First run: batch contains 1 image
- Second run: batch contains 2 images  
- Third run: batch contains 3 images
- Use accumulated batch for batch processing
```

### Example 2: Conditional Batch Building

**Workflow**: Add images to a batch only when certain conditions are met

```
Setup:
- Conditional node determines if image should be added
- Use Conditional Validator to pass/block images
- Batch Append accumulates valid images

Flow:
- Valid images get accumulated
- Invalid images are skipped
- Final batch contains only valid items
```

### Example 3: Latent Accumulation

**Workflow**: Collect latent tensors for batch encoding

```
Setup:
- Generate latents in a loop
- Feed each latent to Batch Append (item input)
- batch input: not connected

Result:
- Automatically concatenates latent samples
- {'samples': [N, 4, H/8, W/8]} grows with each iteration
- Feed accumulated batch to VAE Decode
```

### Example 4: Manual Batch Extension

**Workflow**: Add one item to an existing batch

```
Setup:
- Existing batch connected to batch input
- New item connected to item input

Result:
- Returns batch with new item appended
- Internal collection is reset (since external batch is used)
```

## Tips and Best Practices

1. **Reset Accumulation**: To reset the internal collection, either:
   - Change the item type
   - Connect a batch input temporarily
   - Restart the workflow

2. **Type Consistency**: Keep item types consistent for tensor concatenation. Mixed types will be converted to lists.

3. **Memory Management**: Large accumulated batches consume memory. Consider processing in chunks for very large workflows.

4. **Tensor Shape Compatibility**: When appending tensors, ensure dimensions beyond the batch dimension match (e.g., same H, W, C for images).

5. **None vs Disconnected**: Understand the difference:
   - **Disconnected**: Accumulates persistently
   - **None (connected)**: Creates fresh single-item collection each time

6. **Debugging**: Check the console logs to see what the node is doing:
   - "Created internal collection" = Started new accumulation
   - "Appended to internal collection" = Added to existing accumulation
   - "Item type changed" = Reset due to type mismatch

## Technical Details

### Node Properties
- **Category**: `basify`
- **Return Type**: `*` (any type)
- **Internal State**: Maintains collection across executions
- **Thread Safety**: Instance-based state (one state per node instance)

### Logging
The node provides detailed console logging with color-coded messages:
- Blue: Node name identifier
- Green: Success operations with size information
- Includes operation type and collection size where applicable

## Troubleshooting

### Issue: Collection not accumulating
**Cause**: Batch input might be connected (even if empty)  
**Solution**: Ensure batch input is completely disconnected for accumulation mode

### Issue: Type errors when appending
**Cause**: Incompatible tensor shapes or types  
**Solution**: Ensure items have compatible shapes; mixed types will convert to lists

### Issue: Collection resets unexpectedly
**Cause**: Item type changed between executions  
**Solution**: This is intentional behavior; keep item types consistent

### Issue: Memory growing too large
**Cause**: Accumulating too many items without reset  
**Solution**: Periodically reset by changing types or processing the batch

## Related Nodes

- **Display Anything**: View accumulated batch contents
- **Image Selector**: Select specific items from accumulated batch
- **Conditional Validator**: Control when items are accumulated
- **Directory Auto Iterator**: Source items for accumulation

## Version History

- **v1.0**: Initial release with internal accumulation, type detection, and flexible batch handling
