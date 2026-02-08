import os
import json
import random
import logging
from typing import Any, cast, Protocol

try:
    import torch  # type: ignore[import]
except Exception:  # pragma: no cover - runtime import may not be available
    torch = None

try:
    from PIL import Image as PILImage  # type: ignore[import]
    from PIL.PngImagePlugin import PngInfo as PILPngInfo  # type: ignore[import]
    import numpy as np  # type: ignore[import]
    pil_available = True
    numpy_available = True
except Exception:  # pragma: no cover
    pil_available = False
    numpy_available = False

try:
    import folder_paths  # type: ignore[import]
    folder_paths_available = True
except Exception:  # pragma: no cover
    folder_paths_available = False

logger = logging.getLogger(__name__)


# Type protocols for static analysis
class FolderPathsProtocol(Protocol):
    """Type protocol for folder_paths module."""
    
    @staticmethod
    def get_temp_directory() -> str: ...
    
    @staticmethod
    def get_save_image_path(
        prefix: str, output_dir: str, width: int, height: int
    ) -> tuple[str, str, int, str, str]: ...


class PILImageProtocol(Protocol):
    """Type protocol for PIL Image module."""
    
    @staticmethod
    def fromarray(arr: Any, mode: str | None = None) -> Any: ...


class NumpyProtocol(Protocol):
    """Type protocol for numpy module."""
    
    class uint8: ...
    
    @staticmethod
    def clip(a: Any, a_min: Any, a_max: Any) -> Any: ...


# Provide lightweight fallbacks for dependencies so static analysis doesn't error
if not pil_available:  # pragma: no cover - fallback for static analyzers
    class _PILImageFallback:
        @staticmethod
        def fromarray(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("PIL not installed; Image.fromarray unavailable")
    
    class _PngInfoFallback:
        def __init__(self) -> None:
            raise RuntimeError("PIL not installed; PngInfo unavailable")
        
        def add_text(self, key: str, value: str) -> None:
            pass
    
    PILImage = _PILImageFallback()
    PILPngInfo = _PngInfoFallback

if not numpy_available:  # pragma: no cover - fallback for static analyzers
    class _NumpyFallback:
        class uint8:
            pass
        
        @staticmethod
        def clip(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("numpy not installed; np.clip unavailable")
    
    np = _NumpyFallback()

if not folder_paths_available:  # pragma: no cover - fallback for static analyzers
    class _FolderPathsFallback:
        @staticmethod
        def get_temp_directory() -> str:
            return "/tmp"
        
        @staticmethod
        def get_save_image_path(
            prefix: str, output_dir: str, width: int, height: int
        ) -> tuple[str, str, int, str, str]:
            raise RuntimeError("folder_paths not available")
    
    folder_paths = _FolderPathsFallback()


class Colors:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ENDC = '\033[0m'


loggerName = f"{Colors.BLUE}BASIFY VAEDecodePreview{Colors.ENDC}"


class VAEDecodePreview:
    """
    A ComfyUI node that combines VAE decoding and image preview in a single step.
    
    This node decodes latent representations back into pixel space images using a VAE
    and automatically displays them in the ComfyUI interface. It combines the 
    functionality of VAEDecode and PreviewImage nodes into one streamlined operation.
    
    Features:
    - Decodes latent tensors to images using VAE
    - Automatically previews decoded images in ComfyUI
    - Returns the decoded image for downstream nodes
    - Supports batch processing
    - Saves previews to temp directory
    - Includes workflow metadata in saved images
    """
    
    def __init__(self) -> None:
        """Initialize the node with temp directory settings."""
        folder_paths_typed = cast(FolderPathsProtocol, folder_paths)
        self.output_dir: str = folder_paths_typed.get_temp_directory()
        self.type: str = "temp"
        self.prefix_append: str = "_temp_" + ''.join(random.choice("abcdefghijklmnopqrstupvxyz") for _ in range(5))
        self.compress_level: int = 1
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        """Define input parameters for the node."""
        return {
            "required": {
                "samples": ("LATENT", {
                    "tooltip": "The latent tensor to be decoded and previewed"
                }),
                "vae": ("VAE", {
                    "tooltip": "The VAE model used for decoding the latent"
                })
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }
    
    RETURN_TYPES = ("IMAGE",)
    OUTPUT_TOOLTIPS = ("The decoded image, available for downstream nodes",)
    FUNCTION = "decode_and_preview"
    OUTPUT_NODE = True
    CATEGORY = "basify"
    DESCRIPTION = "Decodes latent images back into pixel space and previews them in one step. Combines VAEDecode and PreviewImage functionality for a streamlined workflow."
    
    def decode_and_preview(self, vae: Any, samples: dict[str, Any], prompt: Any = None, extra_pnginfo: Any = None) -> dict[str, Any]:
        """
        Decode latent to image and create preview.
        
        Args:
            vae: The VAE model for decoding
            samples: Dictionary containing the latent samples
            prompt: Optional workflow prompt metadata
            extra_pnginfo: Optional additional PNG metadata
            
        Returns:
            Dictionary with UI preview info and the decoded image tensor
        """
        try:
            # Decode latent to image (from VAEDecode logic)
            latent = samples["samples"]
            
            # Handle nested latents
            if hasattr(latent, 'is_nested') and latent.is_nested:
                latent = latent.unbind()[0]
            
            # Decode using VAE
            images = vae.decode(latent)
            
            # Combine batches if needed (5D tensor to 4D)
            if len(images.shape) == 5:
                images = images.reshape(-1, images.shape[-3], images.shape[-2], images.shape[-1])
            
            # Save and preview the decoded images
            preview_result = self._save_images(images, prompt=prompt, extra_pnginfo=extra_pnginfo)
            
            logger.info(f"[{loggerName}] Successfully decoded and previewed {images.shape[0]} image(s)")
            
            # Return both UI preview and the image tensor for downstream use
            return {"ui": preview_result["ui"], "result": (images,)}
            
        except Exception as e:
            logger.error(f"[{loggerName}] Failed to decode and preview: {e}")
            raise e
    
    def _save_images(self, images: Any, prompt: Any = None, extra_pnginfo: Any = None) -> dict[str, Any]:
        """
        Save images to temp directory for preview (adapted from SaveImage).
        
        Args:
            images: Tensor of images to save
            prompt: Optional workflow prompt
            extra_pnginfo: Optional additional metadata
            
        Returns:
            Dictionary with UI preview information
        """
        filename_prefix: str = "ComfyUI" + self.prefix_append
        
        # Get save path using properly typed folder_paths
        folder_paths_typed = cast(FolderPathsProtocol, folder_paths)
        full_output_folder: str
        filename: str
        counter: int
        subfolder: str
        
        full_output_folder, filename, counter, subfolder, _ = folder_paths_typed.get_save_image_path(
            filename_prefix,
            self.output_dir,
            images[0].shape[1],
            images[0].shape[0]
        )
        
        results: list[dict[str, str]] = []
        
        pil_image_typed = cast(PILImageProtocol, PILImage)
        numpy_typed = cast(NumpyProtocol, np)
        
        for batch_number, image in enumerate(images):
            # Convert tensor to numpy array and then to PIL Image
            i = 255. * image.cpu().numpy()
            clipped = numpy_typed.clip(i, 0, 255)
            img = pil_image_typed.fromarray(clipped.astype(numpy_typed.uint8))
            
            # Add workflow metadata
            metadata: Any = None
            try:
                from comfy.cli_args import args  # type: ignore[import]
                # Check if metadata should be added - use cast to handle unknown type
                args_obj = cast(Any, args)
                disable_metadata: bool = getattr(args_obj, 'disable_metadata', False)
                if not disable_metadata:
                    metadata = PILPngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for key in extra_pnginfo:
                            metadata.add_text(key, json.dumps(extra_pnginfo[key]))
            except Exception:
                # If metadata fails, continue without it
                pass
            
            # Save image
            filename_with_batch_num: str = filename.replace("%batch_num%", str(batch_number))
            file: str = f"{filename_with_batch_num}_{counter:05}_.png"
            file_path: str = os.path.join(full_output_folder, file)
            
            img.save(file_path, pnginfo=metadata, compress_level=self.compress_level)
            
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1
        
        return {"ui": {"images": results}}


# Registration
NODE_CLASS_MAPPINGS = {
    "BasifyVAEDecodePreview": VAEDecodePreview
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyVAEDecodePreview": "Basify: VAE Decode & Preview"
}
