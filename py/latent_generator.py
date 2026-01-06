import torch
from typing import Any
import comfy.model_management

class LatentGenerator:
    """
    A ComfyUI node for generating empty latent tensors with predefined or manual resolutions.
    
    Features:
    - Toggle between predefined resolutions and manual width/height input
    - Configurable batch size
    - Standard ComfyUI latent format output
    """
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        # Predefined resolutions organized by common aspect ratios
        predefined_resolutions = [
            # Square (1:1) - Most versatile
            "512×512 (1:1) - Small square",
            "768×768 (1:1) - Standard square",
            "832×832 (1:1) - Medium square", 
            "1024×1024 (1:1) - Large square",
            
            # Portrait (3:4) - Classic portrait format
            "576×768 (3:4) - Small portrait",
            "672×896 (3:4) - Medium portrait",
            "768×1024 (3:4) - Portrait",
            
            # Landscape (4:3) - Classic landscape format
            "768×576 (4:3) - Small landscape",
            "896×672 (4:3) - Medium landscape",
            "1024×768 (4:3) - Landscape",
            
            # Widescreen (16:9) - Cinematic/video format
            "896×512 (16:9) - Small widescreen",
            "1152×648 (16:9) - Medium widescreen",
            "1344×768 (16:9) - Widescreen",
            "1536×864 (16:9) - Widescreen large",
            
            # Vertical video (9:16) - Mobile/social media
            "512×896 (9:16) - Small vertical",
            "648×1152 (9:16) - Medium vertical",
            "768×1344 (9:16) - Vertical",
            "864×1536 (9:16) - Vertical large",
            
            # Photo (2:3) - Standard photo format
            "576×832 (2:3) - Small photo portrait",
            "704×1024 (2:3) - Medium photo portrait",
            "832×1216 (2:3) - Photo portrait",
            
            # Photo landscape (3:2)
            "832×576 (3:2) - Small photo landscape",
            "1024×704 (3:2) - Medium photo landscape",
            "1216×832 (3:2) - Photo landscape",
            
            # Golden ratio (5:8 / 8:5)
            "832×1280 (5:8) - Golden portrait",
            "1280×832 (8:5) - Golden landscape"
        ]
        
        return {
            "required": {
                "resolution_mode": (["predefined", "manual"], {"default": "predefined"}),
                "predefined_resolution": (predefined_resolutions, {"default": "768×1024 (3:4) - Portrait"}),
                "manual_width": ("INT", {"default": 512, "min": 16, "max": 16384, "step": 8}),
                "manual_height": ("INT", {"default": 768, "min": 16, "max": 16384, "step": 8}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 4096}),
            }
        }
    
    @classmethod
    def VALIDATE_INPUTS(cls, resolution_mode: str, predefined_resolution: str, manual_width: int, manual_height: int, batch_size: int) -> bool | str:
        if resolution_mode == "manual":
            # Validate manual dimensions are multiples of 8 (required for latent space division)
            if manual_width % 8 != 0:
                return f"Manual width must be a multiple of 8, got {manual_width}"
            if manual_height % 8 != 0:
                return f"Manual height must be a multiple of 8, got {manual_height}"
        return True

    RETURN_TYPES = ("LATENT", "INT", "INT")
    RETURN_NAMES = ("latent", "width", "height")
    FUNCTION = "generate_latent"
    CATEGORY = "latent"

    def generate_latent(self, resolution_mode: str, predefined_resolution: str, manual_width: int, manual_height: int, batch_size: int) -> tuple[dict[str, torch.Tensor], int, int]:
        # Determine width and height based on mode
        if resolution_mode == "predefined":
            # Parse predefined resolution (format: "width×height (aspect) - description")
            try:
                resolution_part = predefined_resolution.split(" ")[0]  # Get "width×height" part
                width_str, height_str = resolution_part.split("×")
                width = int(width_str)
                height = int(height_str)
            except (ValueError, IndexError) as e:
                raise ValueError(f"Failed to parse predefined resolution '{predefined_resolution}': {e}")
        else:  # manual mode
            # Use manual dimensions (already validated to be multiples of 8)
            width = manual_width
            height = manual_height
        
        try:
            # Get device at runtime for better flexibility
            device = comfy.model_management.intermediate_device()  # type: ignore[no-any-return]
            
            # Generate latent tensor
            # Standard latent format: [batch_size, channels, height//8, width//8]
            latent = torch.zeros([batch_size, 4, height // 8, width // 8], device=device)  # type: ignore[arg-type]
            
            return ({"samples": latent}, width, height)
        
        except Exception as e:
            # Clean up and force garbage collection on error
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise e

# Registration
NODE_CLASS_MAPPINGS = {
    "BasifyLatentGenerator": LatentGenerator
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyLatentGenerator": "Basify: Latent Generator"
}
