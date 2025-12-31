# Sound Notifier 🔔 - Documentation

A ComfyUI node that plays a sound notification when executed, perfect for alerting you when a workflow completes.

## Features

- **Workflow Completion Alerts** - Get notified when your generation finishes
- **Universal Input** - Accepts any output type (IMAGE, LATENT, STRING, etc.) as trigger
- **Test Button** - Preview sound before running workflow
- **Volume Control** - Adjust notification volume (0-100%)
- **Enable/Disable Toggle** - Easily turn notifications on/off
- **Multi-Format Support** - Plays WAV, MP3, OGG, and other common formats
- **Terminal Node** - No output, designed to be the final node in a chain

---

## Input Parameters

### Required Inputs

#### `sound_file` (STRING)
Path to the sound file to play.

**Default:** `~/Music/that-was-quick.mp3`

**Supported Formats:** WAV, MP3, OGG, FLAC, and other formats supported by pygame.mixer

**Path Features:**
- Supports `~` for home directory expansion
- Use absolute paths: `/path/to/sound.mp3`
- Or relative to home: `~/Music/notification.wav`

**Examples:**
```
~/Music/that-was-quick.mp3
/usr/share/sounds/freedesktop/stereo/complete.oga
~/Downloads/notification.wav
```

#### `volume` (INT)
Volume level for the notification sound.

**Range:** 0-100  
**Default:** 100  
**Step:** 1

- **0** - Muted (no sound plays)
- **50** - Half volume
- **100** - Full volume

#### `enabled` (DROPDOWN)
Enable or disable sound playback.

**Options:** `enable`, `disable`  
**Default:** `enable`

Useful for temporarily disabling notifications without removing the node or changing connections.

### Optional Inputs

#### `trigger` (ANY)
Universal input that accepts any type from a previous node.

**Type:** IO.ANY - accepts IMAGE, LATENT, STRING, INT, FLOAT, and all other types  
**Default:** None

Connect this to the output of your final node to trigger the sound when that node completes execution.

---

## Output Parameters

**None** - This is a terminal node with no outputs. It's designed to be placed at the end of your workflow chain.

---

## Usage Examples

### Basic Usage - Workflow Completion

```
[Generate Image] → [Save Image] → [Sound Notifier]
```

1. Add a Sound Notifier node to your workflow
2. Connect the output of your final node to the `trigger` input
3. Set your preferred sound file and volume
4. Run the workflow - you'll hear a sound when it completes!

### Testing Sound Before Workflow

Use the **🔊 Test Sound** button in the node to preview your sound without running the entire workflow. This is useful for:
- Checking if the sound file path is correct
- Adjusting volume to a comfortable level
- Testing different sound files

### Multiple Workflow Stages

```
[Generate] → [Process A] → [Sound Notifier #1 (quiet)]
                         ↓
                    [Process B] → [Sound Notifier #2 (loud)]
```

You can use multiple Sound Notifier nodes at different stages, each with different sounds and volumes.

### Conditional Notifications

Set `enabled` to `disable` when you don't want notifications (e.g., during testing), then switch back to `enable` for production runs.

---

## Technical Details

### Sound Playback
- Uses pygame.mixer for reliable cross-platform audio
- Non-blocking playback (workflow execution completes immediately)
- Global mixer initialization (shared across all instances)
- Each node loads its own Sound object for independent control

### Execution Behavior
- **OUTPUT_NODE = True**: Executes even without downstream connections
- **RETURN_TYPES = ()**: No outputs (terminal node)
- Requires an input connection to be included in workflow execution graph
- Accepts any input type via ComfyUI's IO.ANY type system

### Performance
- Minimal overhead (mixer initializes only once)
- Sound loading happens at execution time
- Non-blocking playback doesn't slow down workflow
- Small memory footprint

### Error Handling
- Gracefully handles missing sound files (logs error, continues workflow)
- Continues execution even if pygame fails to initialize
- Always completes successfully (errors logged but not raised)

---

## Troubleshooting

### Sound Doesn't Play

**Check the file path:**
- Verify the file exists: `ls -l ~/Music/that-was-quick.mp3`
- Check ComfyUI console for error messages
- Ensure the path uses `/` (not `\`) on all platforms

**Verify pygame installation:**
```bash
conda activate ComfyUI
pip install pygame>=2.5.0
```

**Check enabled status:**
- Ensure `enabled` is set to `enable`, not `disable`

**Verify ComfyUI is running locally:**
- Sound plays on the **server** where ComfyUI is running
- If ComfyUI is on a remote server, you won't hear the sound locally

### Volume Too Loud/Quiet

- Adjust the `volume` parameter (0-100)
- Also check your system volume settings
- Try different sound files (some are normalized differently)
- Use the test button to preview volume before running workflow

### Node Doesn't Execute

- Ensure the `trigger` input is connected to another node's output
- The node won't execute if it's not connected (even with OUTPUT_NODE = True)
- Check that the workflow path includes this node

### File Format Not Supported

pygame.mixer supports most common formats, but some require additional codecs:
- **Always works:** WAV, OGG
- **Usually works:** MP3 (requires pygame 2.0+)
- **May need codecs:** FLAC, other formats

If you have issues, convert your sound to WAV or OGG format.

---

## Integration Tips

### Best Practices

1. **Placement:** Add Sound Notifier as the last node in your workflow
2. **Volume:** Start with volume at 50-70% to avoid jarring notifications
3. **Sound Selection:** Use short sounds (0.5-2 seconds) for quick feedback
4. **Testing:** Use the test button during setup, disable during rapid iteration

### Recommended Workflow Pattern

```
[Your Workflow Nodes]
         ↓
   [Final Output] ──trigger──→ [Sound Notifier]
```

This ensures the sound plays only when everything completes successfully.

### Finding Sound Files

**Linux:**
- System sounds: `/usr/share/sounds/`
- User sounds: `~/Music/` or `~/Sounds/`

**macOS:**
- System sounds: `/System/Library/Sounds/`
- User sounds: `~/Music/`

**Windows:**
- System sounds: `C:\Windows\Media\`
- User sounds: `C:\Users\YourName\Music\`

### Creating Custom Sounds

Use short, distinctive sounds:
- Export from audio editors as WAV or OGG
- Keep file sizes small (<1 MB)
- Normalize volume for consistency

---

## Example Configuration

```python
{
  "sound_file": "~/Music/that-was-quick.mp3",
  "volume": 75,
  "enabled": "enable",
  "trigger": [connection from previous node]
}
```

---

## Dependencies

- **pygame** >= 2.5.0 (installed automatically with basify)

---

## Notes

- Sound plays asynchronously (doesn't block the workflow)
- Thread-safe for concurrent workflow execution
- Minimal CPU/memory overhead
- Works on Linux, macOS, and Windows
- Sound plays on the **server**, not in your browser

For issues or feature requests, please file an issue on the basify repository.
