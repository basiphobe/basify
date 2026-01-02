# Sound Notifier

## Overview

The **Sound Notifier** is a ComfyUI custom node that plays an audio notification when executed in a workflow. This is particularly useful for alerting you when long-running workflows complete, enabling you to work on other tasks without constantly monitoring your workflow progress.

## Key Features

- **Audio Notifications**: Plays a sound when the node executes
- **Multiple Formats**: Supports WAV, MP3, and OGG audio files
- **Volume Control**: Adjustable volume from 0-100%
- **Enable/Disable Toggle**: Easily turn notifications on or off without removing the node
- **Trigger Input**: Optional input to control execution timing
- **Path Expansion**: Supports `~` for home directory paths
- **Non-Blocking**: Sound plays asynchronously without delaying workflow execution

## Node Information

- **Node Name**: `BasifySoundNotifier`
- **Display Name**: `Basify: Sound Notifier`
- **Category**: `basify`
- **Output Node**: Yes (executes at workflow end)

## Input Parameters

### Required Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sound_file` | STRING | `"~/Music/that-was-quick.mp3"` | Path to the audio file to play |
| `volume` | INT | `100` | Volume level (0-100, where 100 is maximum) |
| `enabled` | DROPDOWN | `"enable"` | Enable or disable sound playback (`enable`/`disable`) |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trigger` | ANY | None | Optional input to control when the node executes |

## Output Values

This node has no outputs. It's designed as an OUTPUT_NODE that executes at the end of the workflow.

## Supported Audio Formats

- **WAV** (`.wav`) - Uncompressed audio
- **MP3** (`.mp3`) - Compressed audio
- **OGG** (`.ogg`) - Ogg Vorbis compressed audio

## How It Works

### Audio Engine

The node uses **pygame.mixer** for audio playback:
- Initialized once globally on first use
- Configuration: 44.1kHz, 16-bit, stereo, 512-byte buffer
- Thread-safe initialization with mutex locking

### Execution Flow

1. **Check Enabled Status**: If `enabled` is `"disable"`, the node exits immediately
2. **Initialize Audio**: Ensures pygame.mixer is initialized (one-time setup)
3. **Path Expansion**: Expands `~` to the user's home directory
4. **File Validation**: Checks if the sound file exists
5. **Load Audio**: Loads the sound file into memory
6. **Set Volume**: Applies the volume level (0.0-1.0 scale)
7. **Play Sound**: Starts audio playback asynchronously
8. **Complete**: Node execution finishes (sound plays in background)

### Non-Blocking Playback

The sound plays asynchronously, so:
- Workflow execution completes immediately
- ComfyUI remains responsive
- Sound continues playing even after workflow finishes

## Usage Examples

### Basic Usage

Place the Sound Notifier at the end of your workflow:

```
[Image Processing Nodes] -> [Save Image] -> [Sound Notifier]
```

The sound will play when the workflow completes.

### Using the Trigger Input

Connect the trigger input to control execution timing:

```
[Any Node Output] -> [trigger input of Sound Notifier]
```

The Sound Notifier will execute after the connected node completes.

### Multiple Notifications

Use multiple Sound Notifier nodes with different sounds for different workflow paths:

```
[Branch A] -> [Sound Notifier (success sound)]
[Branch B] -> [Sound Notifier (error sound)]
```

### Temporary Disable

To temporarily disable notifications without removing the node:
- Set `enabled` to `"disable"`
- The node will execute but produce no sound
- No need to disconnect or delete the node

## Configuration Examples

### Subtle Background Notification
```
sound_file: ~/Music/gentle-chime.wav
volume: 30
enabled: enable
```

### Loud Completion Alert
```
sound_file: ~/Music/loud-alarm.mp3
volume: 100
enabled: enable
```

### Custom Sound Library
```
sound_file: /path/to/custom/sounds/workflow-complete.ogg
volume: 75
enabled: enable
```

## Path Specifications

### Home Directory Expansion
The node supports `~` expansion:
- `~/Music/sound.mp3` → `/home/username/Music/sound.mp3`
- `~/sounds/alert.wav` → `/home/username/sounds/alert.wav`

### Absolute Paths
You can also use absolute paths:
- `/usr/share/sounds/complete.wav`
- `/opt/audio/notifications/done.mp3`

### Relative Paths
Relative paths work but are not recommended:
- Resolved relative to ComfyUI's working directory
- Can be unpredictable depending on how ComfyUI is launched

## Best Practices

### 1. Use Appropriate Sounds
- **Short sounds** (1-3 seconds) work best for notifications
- Avoid long audio tracks that may be distracting
- Consider pleasant, non-jarring sounds for frequent workflows

### 2. Set Reasonable Volume
- Start with 50-75% volume and adjust as needed
- Consider your environment (office vs. home)
- Lower volume for frequent workflow executions

### 3. Organize Your Sound Files
Create a dedicated sounds directory:
```
~/Music/comfyui-sounds/
  ├── success.mp3
  ├── error.wav
  ├── warning.ogg
  └── complete.mp3
```

### 4. Test Before Long Workflows
- Run a quick test workflow to verify sound plays
- Check volume level is appropriate
- Ensure file path is correct

### 5. Use Enable/Disable for Development
When developing workflows:
- Keep the node but set `enabled` to `"disable"`
- Re-enable for production or long-running workflows

### 6. Position at Workflow End
Place the Sound Notifier node:
- After save operations complete
- At the final output node
- Connected to nodes that signify true completion

## Error Handling

The node handles errors gracefully:

### File Not Found
```
[ERROR] Sound file not found: /path/to/missing/file.mp3
```
- Workflow continues without playing sound
- Error logged to console
- No workflow interruption

### Invalid Audio Format
```
[ERROR] Error playing sound: Unable to load sound file
```
- Workflow continues
- Check file format is supported (WAV, MP3, OGG)
- Verify file is not corrupted

### Pygame Initialization Failure
```
[ERROR] Failed to initialize pygame.mixer: ...
```
- Occurs if pygame is not installed or system audio is unavailable
- Workflow continues without sound
- Check pygame installation: `pip install pygame`

## Troubleshooting

### No Sound Playing

**Check enabled status:**
- Verify `enabled` is set to `"enable"`

**Verify file path:**
- Ensure the file exists at the specified location
- Try using an absolute path for testing
- Check file permissions (must be readable)

**Test audio file:**
- Verify the file plays in a standard audio player
- Ensure format is supported (WAV, MP3, OGG)

**Check system audio:**
- Ensure system volume is not muted
- Test with other applications that produce sound
- On Linux, verify ALSA/PulseAudio is working

### Import Error

**Pygame not installed:**
```bash
pip install pygame
```

**In conda environment:**
```bash
conda install pygame
```

### Volume Too Quiet/Loud

- Adjust the `volume` parameter (0-100)
- Check system volume settings
- Try a different audio file

### Sound Cuts Off

- The sound plays asynchronously and may be interrupted if:
  - ComfyUI closes immediately after workflow
  - System audio is stopped
- For critical notifications, use longer sounds or add a delay node

## Integration Examples

### Basic Completion Notification
```
[Workflow] -> [Save Image] -> [Sound Notifier]
```

### Conditional Notifications
```
[Processing] -> [If Success] -> [Sound Notifier (success.mp3)]
                             -> [If Failed] -> [Sound Notifier (error.mp3)]
```

### With Status Display
```
[Workflow] -> [Sound Notifier]
           -> [Status Display]
```

### Batch Processing Alert
```
[Directory Auto Iterator] -> [Processing] -> [Save Image]
                          -> [completed] -> [Sound Notifier]
```
Use the completed flag from Directory Auto Iterator to play sound only when all images are processed.

## Technical Notes

### Pygame.mixer Configuration
- **Frequency**: 44.1 kHz (CD quality)
- **Bit depth**: 16-bit signed
- **Channels**: 2 (stereo)
- **Buffer size**: 512 bytes (low latency)

### Thread Safety
- Mixer initialization uses a global lock (`_mixer_lock`)
- Prevents race conditions when multiple workflows execute simultaneously
- Initialization happens once per ComfyUI session

### Volume Scaling
- Input volume (0-100) is converted to pygame scale (0.0-1.0)
- Formula: `pygame_volume = volume / 100.0`
- Linear scaling (not logarithmic)

### Logging
All operations are logged with `[BASIFY Sound Notifier]` prefix:
- Info: Successful playback, initialization
- Error: File not found, playback errors, initialization failures

## Dependencies

### Required
- **pygame** - Audio playback library
  ```bash
  pip install pygame
  ```

### Optional
- None - All dependencies are required for functionality

## Compatibility

- **ComfyUI**: Compatible with standard ComfyUI workflows
- **Operating Systems**: 
  - Linux (ALSA, PulseAudio, PipeWire)
  - Windows (DirectSound, WASAPI)
  - macOS (CoreAudio)
- **Python**: Python 3.7+
- **Audio Formats**: WAV, MP3, OGG (via pygame.mixer)

## Performance Considerations

- **Memory**: Audio file loaded into memory (keep files small)
- **Initialization**: One-time setup cost on first use
- **Playback**: Non-blocking, minimal CPU overhead
- **File Size**: Recommended < 5MB per sound file
- **Workflow Impact**: Negligible (< 10ms overhead typically)

## Common Use Cases

### 1. Long Training/Generation Workflows
Alert when stable diffusion batches complete:
```
[SD Model] -> [Batch Processing] -> [Save] -> [Sound Notifier]
```

### 2. Overnight Rendering
Get notified when morning renders finish:
```
[Complex Workflow] -> [Final Output] -> [Sound Notifier (loud alarm)]
```

### 3. Development Testing
Disable during development, enable for production:
```
enabled: disable  # During development
enabled: enable   # For production runs
```

### 4. Multi-Stage Workflows
Different sounds for different completion stages:
```
[Stage 1] -> [Sound 1 (chime)]
[Stage 2] -> [Sound 2 (bell)]
[Final]   -> [Sound 3 (fanfare)]
```

## Finding Sound Files

### Free Sound Resources
- **System Sounds**: Check `/usr/share/sounds/` on Linux
- **Online Libraries**: 
  - FreeSound.org
  - Zapsplat.com (free tier)
  - Notification Sounds (search online)

### Creating Custom Sounds
- Use Audacity (free) to create/edit sounds
- Keep sounds short (1-3 seconds)
- Export as WAV for compatibility or MP3 for smaller size

### Recommended Sound Characteristics
- Duration: 1-3 seconds
- Format: WAV (best compatibility) or MP3 (smaller size)
- Frequency: Clear tones in 500-2000 Hz range
- Avoid: Sudden loud peaks, harsh tones, copyrighted material

## Advanced Usage

### Dynamic Sound Selection
While this node doesn't support dynamic sound selection directly, you can:
- Use multiple Sound Notifier nodes with different sounds
- Route workflow execution to different notifiers based on conditions

### Volume Automation
To vary volume based on time of day or conditions:
- Set volume parameter before workflow execution
- Use lower volume for night/early morning (30-50)
- Use higher volume for daytime (70-100)

### Silent Mode
For environments where sound is inappropriate:
- Set `enabled` to `"disable"`
- Consider visual notifications instead (status display, file output)

## Migration Notes

If upgrading from a custom notification solution:
- This node replaces manual sound playback scripts
- Pygame.mixer is more reliable than system command calls
- Volume control is built-in (no need for external tools)

## Future Enhancements

Potential future features (not currently implemented):
- Sound file browser/picker
- Preview button to test sound before workflow
- Multiple sound file selection
- Fade in/fade out effects
- Repeat count option
- Delay before playback

## Support

For issues or questions:
1. Check console logs for error messages
2. Verify pygame installation
3. Test audio file in a standard player
4. Check file path and permissions
5. Review this documentation for troubleshooting steps
