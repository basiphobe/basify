# Timer Display

## Overview

The **Timer Display** node is a visual runtime monitor for ComfyUI workflows. It shows elapsed execution time directly on the node in a large canvas-rendered font, making it easy to see how long a workflow branch took without opening logs or inspecting the queue UI.

The node is designed to sit at the end of a workflow branch as a passthrough output node. It preserves the final elapsed time after completion so you can review the runtime until the next execution actually begins.

## Key Features

- **Large On-Node Timer**: Renders elapsed time directly on the node body
- **Adjustable Text Size**: Built-in slider to control timer text scale
- **Passthrough Design**: Optional `trigger` input and matching output for easy workflow chaining
- **Start-On-Execution**: Resets only when real execution activity begins
- **Final Time Persistence**: Keeps the last runtime visible after completion
- **Success/Error States**: Uses different colors while running and on failure
- **Auto Resizing**: Expands node dimensions to fit the current timer text size

## Node Information

- **Node Name**: `BasifyTimerDisplay`
- **Display Name**: `Basify: Timer Display`
- **Category**: `basify`
- **Output Node**: Yes

## Input Parameters

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trigger` | ANY | None | Connect this to the end of a workflow branch so the timer node participates in execution |

## Output Values

| Output | Type | Description |
|--------|------|-------------|
| `trigger` | ANY | Passes through the connected trigger value unchanged |

## Frontend Controls

| Control | Type | Default | Description |
|---------|------|---------|-------------|
| `text_size` | Slider | `180` | Controls the size of the timer text drawn on the node |

## How It Works

### Execution Lifecycle

The timer listens to ComfyUI frontend execution events and manages its display entirely in JavaScript:

1. **Queue Start**: The node notes that a run has been queued, but does not reset yet
2. **First Execution Activity**: On the first real execution event, the timer resets to `00:00.0` and starts counting
3. **During Execution**: The timer updates every 100ms
4. **Completion**: The final elapsed time remains visible on the node
5. **Next Run**: The display resets only when the next workflow actually begins executing

### Why It Uses a Trigger Input

Unattached output nodes do not automatically execute in ComfyUI. The `trigger` input/output pair lets you place the Timer Display at the end of a branch so it becomes part of the executed graph.

## Usage Examples

### Basic End-of-Workflow Timing

```
[Main Workflow Output] -> [Basify: Timer Display]
```

The node will execute at the end of the branch and show the total elapsed runtime.

### Timing After Save Image

```
[KSampler] -> [VAE Decode] -> [Save Image] -> [Basify: Timer Display]
```

This is a good placement if you want the timer to include image decoding and file write time.

### Timing a Specific Branch

```
[Branch A Result] -> [Basify: Timer Display]
[Branch B Result] -> [Another Output Node]
```

Use this when you only care about one branch of a larger graph.

### Reviewing Previous Runtime

After a workflow finishes:

- The final elapsed time remains visible
- You can inspect the result before running again
- The timer resets only when the next run begins execution

## Display States

- **Idle / Complete**: Light neutral text color
- **Running**: Highlighted warm color while execution is in progress
- **Error / Interrupted**: Red text color when execution fails or is interrupted

## Sizing Behavior

The node automatically resizes based on:

- Current timer text length
- Selected `text_size`
- Built-in padding for readability

This prevents the timer text from overflowing when using larger font sizes or when the display format grows longer.

## Time Format

The timer uses two display formats:

- **Under 1 hour**: `MM:SS.t`
- **1 hour or more**: `HH:MM:SS`

Examples:

```
00:12.4
03:47.9
01:02:15
```

## Best Practices

### 1. Place It at the True End

Connect the Timer Display after the last node that matters for your runtime measurement.

### 2. Include Save Operations If Needed

If you care about total wall-clock workflow time, place it after nodes like `Save Image`, not before them.

### 3. Use Separate Timer Nodes for Different Branches

If you want to compare different paths, attach different timer nodes to those branches.

### 4. Adjust Text Size for Your Canvas Zoom

Use the `text_size` slider to keep the timer legible at your normal graph zoom level.

## Troubleshooting

### Timer Does Not Start

- Make sure the node is connected to the executed graph through `trigger`
- Place it at the end of an active workflow branch
- Confirm the workflow path containing the timer actually runs

### Timer Never Executes

If the node is not attached to another node, ComfyUI will not include it in execution.

### Text Overflows

- Increase node size manually if needed
- Lower the `text_size` slider
- Re-add the node if an old saved instance is using outdated frontend state

## Implementation Details

### Python Backend

The backend file is intentionally minimal:

- Defines the node and category
- Exposes the passthrough `trigger` input/output
- Returns the trigger value unchanged

### JavaScript Frontend

The frontend handles:

- Workflow lifecycle event listeners
- Timer state management
- Canvas-based text rendering
- Dynamic node resizing
- Slider-based font size control

This keeps the live timer behavior in the browser, where sub-second updates are practical.