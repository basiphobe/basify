import logging
import server
import os
from aiohttp import web

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)

async def scan_directory_for_checkpoints(request):
    """API endpoint to scan a directory for checkpoint files"""
    payload = None
    checkpoints = None
    visited_paths = None
    
    try:
        payload = await request.json()
        directory_path = payload.get("directory_path", "")
        
        if not directory_path:
            return web.json_response({"error": "No directory path provided"}, status=400)
        
        if not os.path.exists(directory_path):
            return web.json_response({"checkpoints": []})
        
        checkpoint_extensions = ('.ckpt', '.safetensors', '.pt', '.pth')
        checkpoints = []
        visited_paths = set()  # Track visited paths to prevent circular symlink issues
        
        try:
            # Use os.walk with followlinks=True to support symbolic links
            for root, dirs, files in os.walk(directory_path, followlinks=True):
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
            
            # Store result before cleanup
            result = web.json_response({"checkpoints": checkpoints})
            
            # Clean up large data structures
            del checkpoints
            del visited_paths
            del payload
            
            return result
            
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
        # Ensure cleanup even on error
        if checkpoints is not None:
            del checkpoints
        if visited_paths is not None:
            del visited_paths
        if payload is not None:
            del payload

server.PromptServer.instance.app.add_routes([
    web.post("/basify/scan_directory", scan_directory_for_checkpoints),
])
