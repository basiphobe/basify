import os
import logging
import threading
from typing import Any
from comfy.comfy_types.node_typing import IO

logger = logging.getLogger(__name__)

# Global flag to track pygame.mixer initialization
_mixer_initialized = False
_mixer_lock = threading.Lock()

def initialize_mixer():
    """Initialize pygame.mixer once globally."""
    global _mixer_initialized
    with _mixer_lock:
        if not _mixer_initialized:
            try:
                import pygame
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                _mixer_initialized = True
                logger.info("[BASIFY Sound Notifier] pygame.mixer initialized")
            except Exception as e:
                logger.error(f"[BASIFY Sound Notifier] Failed to initialize pygame.mixer: {e}")
                raise

class SoundNotifier:
    """ComfyUI node that plays a sound when executed, useful for workflow completion notifications."""
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "sound_file": ("STRING", {
                    "default": "~/Music/that-was-quick.mp3",
                    "multiline": False,
                    "tooltip": "Path to sound file (wav, mp3, ogg). Supports ~ for home directory."
                }),
                "volume": ("INT", {
                    "default": 100,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "Volume level (0-100)"
                }),
                "enabled": (["enable", "disable"], {
                    "default": "enable",
                    "tooltip": "Enable or disable sound playback"
                }),
            },
            "optional": {
                "trigger": (IO.ANY, {}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "play_sound"
    CATEGORY = "basify"
    OUTPUT_NODE = True

    def play_sound(self, sound_file: str, volume: int, enabled: str, unique_id: str | None = None, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Play a sound notification."""
        
        # If disabled, just pass through
        if enabled == "disable":
            logger.info("[BASIFY Sound Notifier] Sound playback disabled")
            return {}
        
        try:
            # Initialize mixer if needed
            initialize_mixer()
            
            import pygame
            
            # Expand home directory if present
            sound_path = os.path.expanduser(sound_file)
            
            # Check if file exists
            if not os.path.isfile(sound_path):
                logger.error(f"[BASIFY Sound Notifier] Sound file not found: {sound_path}")
                return {}
            
            # Load and play sound
            sound = pygame.mixer.Sound(sound_path)
            sound.set_volume(volume / 100.0)
            sound.play()
            
            logger.info(f"[BASIFY Sound Notifier] Playing: {os.path.basename(sound_path)} at {volume}% volume")
            
        except Exception as e:
            logger.error(f"[BASIFY Sound Notifier] Error playing sound: {e}")
        
        # Return empty dict for OUTPUT_NODE
        return {}


NODE_CLASS_MAPPINGS = {
    "BasifySoundNotifier": SoundNotifier
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifySoundNotifier": "Basify: Sound Notifier"
}
