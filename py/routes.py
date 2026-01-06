import logging
import server
import os
from typing import Any
from aiohttp import web

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)

async def scan_directory_for_checkpoints(request: web.Request) -> web.Response:
    """API endpoint to scan a directory for checkpoint files"""
    payload: Any = None
    checkpoints: list[str] | None = None
    visited_paths: set[str] | None = None
    
    try:
        payload = await request.json()
        directory_path: str = payload.get("directory_path", "")
        
        if not directory_path:
            return web.json_response({"error": "No directory path provided"}, status=400)
        
        if not os.path.exists(directory_path):
            return web.json_response({"checkpoints": []})
        
        checkpoint_extensions = ('.ckpt', '.safetensors', '.pt', '.pth')
        checkpoints = []
        visited_paths = set()  # Track visited paths to prevent circular symlink issues
        
        try:
            # Use os.walk with followlinks=True to support symbolic links
            for root, _dirs, files in os.walk(directory_path, followlinks=True):
                # Prevent infinite loops from circular symlinks
                real_root = os.path.realpath(root)
                if real_root in visited_paths:
                    continue
                visited_paths.add(real_root)
                
                for file in files:
                    if file.lower().endswith(checkpoint_extensions):
                        full_path = os.path.join(root, file)
                        # Resolve symbolic links to get real path
                        real_path = os.path.realpath(full_path)
                        
                        # Create display name with subdirectory if applicable
                        rel_path = os.path.relpath(full_path, directory_path)
                        
                        # Add symbolic link indicator if it's a link
                        if os.path.islink(full_path):
                            rel_path += " → " + os.path.basename(real_path)
                        
                        checkpoints.append(rel_path)
            
            # Sort alphabetically
            checkpoints.sort()
            
            logger.info(f"{Colors.BLUE}[BASIFY Routes]{Colors.ENDC} {Colors.GREEN}Found {len(checkpoints)} checkpoints in {directory_path}{Colors.ENDC}")
            
            # Don't delete here - let finally block handle cleanup
            
            return web.json_response({"checkpoints": checkpoints})
            
        except PermissionError as e:
            logger.warning(f"{Colors.BLUE}[BASIFY Routes]{Colors.ENDC} {Colors.YELLOW}Permission denied scanning {directory_path}: {e}{Colors.ENDC}")
            return web.json_response({"checkpoints": []})
        except OSError as e:
            logger.error(f"{Colors.BLUE}[BASIFY Routes]{Colors.ENDC} {Colors.RED}Error scanning directory {directory_path}: {e}{Colors.ENDC}")
            return web.json_response({"checkpoints": []})
        
    except Exception as e:
        logger.error(f"{Colors.BLUE}[BASIFY Routes]{Colors.ENDC} {Colors.RED}Error in scan_directory_for_checkpoints: {e}{Colors.ENDC}")
        return web.json_response({"error": str(e)}, status=500)
    finally:
        # Ensure cleanup even on error - use try/except since del removes from namespace
        try:
            del checkpoints
        except (NameError, UnboundLocalError):
            pass
        try:
            del visited_paths
        except (NameError, UnboundLocalError):
            pass
        try:
            del payload
        except (NameError, UnboundLocalError):
            pass

async def test_sound(request: web.Request) -> web.Response:
    """API endpoint to test sound playback"""
    try:
        payload: Any = await request.json()
        sound_file: str = payload.get("sound_file", "~/Music/that-was-quick.mp3")
        volume: int = payload.get("volume", 100)
        enabled: str = payload.get("enabled", "enable")
        
        if enabled == "disable":
            logger.info(f"{Colors.BLUE}[BASIFY Sound Test]{Colors.ENDC} {Colors.YELLOW}Sound disabled, skipping test{Colors.ENDC}")
            return web.json_response({"status": "disabled"})
        
        # Import pygame and play sound
        try:
            import pygame
            import threading
            
            # Initialize mixer if needed (same logic as sound_notifier.py)
            _mixer_lock = threading.Lock()
            with _mixer_lock:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                    logger.info(f"{Colors.BLUE}[BASIFY Sound Test]{Colors.ENDC} pygame.mixer initialized")
            
            # Expand home directory
            sound_path = os.path.expanduser(sound_file)
            
            if not os.path.isfile(sound_path):
                logger.error(f"{Colors.BLUE}[BASIFY Sound Test]{Colors.ENDC} {Colors.RED}Sound file not found: {sound_path}{Colors.ENDC}")
                return web.json_response({"error": f"Sound file not found: {sound_path}"}, status=404)
            
            # Load and play sound
            sound = pygame.mixer.Sound(sound_path)
            sound.set_volume(volume / 100.0)
            sound.play()
            
            logger.info(f"{Colors.BLUE}[BASIFY Sound Test]{Colors.ENDC} {Colors.GREEN}Playing test sound: {sound_path} at {volume}% volume{Colors.ENDC}")
            
            return web.json_response({"status": "playing", "file": sound_path})
            
        except Exception as e:
            logger.error(f"{Colors.BLUE}[BASIFY Sound Test]{Colors.ENDC} {Colors.RED}Error playing sound: {e}{Colors.ENDC}")
            import traceback
            traceback.print_exc()
            return web.json_response({"error": str(e)}, status=500)
        
    except Exception as e:
        logger.error(f"{Colors.BLUE}[BASIFY Sound Test]{Colors.ENDC} {Colors.RED}Error in test_sound: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)

server.PromptServer.instance.app.add_routes([
    web.post("/basify/scan_directory", scan_directory_for_checkpoints),
    web.post("/basify/test_sound", test_sound),
])
