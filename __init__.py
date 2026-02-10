import os
from typing import Any
import nodes  # type: ignore[import-not-found]

from .py.save_image import NODE_CLASS_MAPPINGS as save_image_nodes
from .py.save_image import NODE_DISPLAY_NAME_MAPPINGS as save_image_display

from .py.metadata_viewer import NODE_CLASS_MAPPINGS as metadata_nodes
from .py.metadata_viewer import NODE_DISPLAY_NAME_MAPPINGS as metadata_display

from .py.wildcard_processor import NODE_CLASS_MAPPINGS as wildcard_nodes
from .py.wildcard_processor import NODE_DISPLAY_NAME_MAPPINGS as wildcard_display

from .py.latent_generator import NODE_CLASS_MAPPINGS as latent_generator_nodes
from .py.latent_generator import NODE_DISPLAY_NAME_MAPPINGS as latent_generator_display

from .py.directory_checkpoint_scanner import NODE_CLASS_MAPPINGS as directory_scanner_nodes
from .py.directory_checkpoint_scanner import NODE_DISPLAY_NAME_MAPPINGS as directory_scanner_display

from .py.directory_auto_iterator import NODE_CLASS_MAPPINGS as directory_auto_iterator_nodes
from .py.directory_auto_iterator import NODE_DISPLAY_NAME_MAPPINGS as directory_auto_iterator_display

from .py.ollama_node import NODE_CLASS_MAPPINGS as ollama_nodes
from .py.ollama_node import NODE_DISPLAY_NAME_MAPPINGS as ollama_display

from .py.sound_notifier import NODE_CLASS_MAPPINGS as sound_notifier_nodes
from .py.sound_notifier import NODE_DISPLAY_NAME_MAPPINGS as sound_notifier_display

from .py.display_anything import NODE_CLASS_MAPPINGS as display_anything_nodes
from .py.display_anything import NODE_DISPLAY_NAME_MAPPINGS as display_anything_display

from .py.conditional_validator import NODE_CLASS_MAPPINGS as conditional_validator_nodes
from .py.conditional_validator import NODE_DISPLAY_NAME_MAPPINGS as conditional_validator_display

from .py.number_randomizer import NODE_CLASS_MAPPINGS as number_randomizer_nodes
from .py.number_randomizer import NODE_DISPLAY_NAME_MAPPINGS as number_randomizer_display

from .py.latent_upscaler import NODE_CLASS_MAPPINGS as latent_upscaler_nodes
from .py.latent_upscaler import NODE_DISPLAY_NAME_MAPPINGS as latent_upscaler_display

from .py.llm_image_refine import NODE_CLASS_MAPPINGS as llm_image_refine_nodes
from .py.llm_image_refine import NODE_DISPLAY_NAME_MAPPINGS as llm_image_refine_display

from .py.vae_decode_preview import NODE_CLASS_MAPPINGS as vae_decode_preview_nodes
from .py.vae_decode_preview import NODE_DISPLAY_NAME_MAPPINGS as vae_decode_preview_display

from .py.lazy_conditional_switch import NODE_CLASS_MAPPINGS as lazy_conditional_switch_nodes
from .py.lazy_conditional_switch import NODE_DISPLAY_NAME_MAPPINGS as lazy_conditional_switch_display

from .py.mask_combiner import NODE_CLASS_MAPPINGS as mask_combiner_nodes
from .py.mask_combiner import NODE_DISPLAY_NAME_MAPPINGS as mask_combiner_display

# Import routes to register web endpoints (no exports needed)
from .py import routes  # noqa: F401  # type: ignore[unused-ignore]

NODE_CLASS_MAPPINGS: dict[str, type[Any]] = {
    **save_image_nodes,
    **metadata_nodes,
    **wildcard_nodes,
    **latent_generator_nodes,
    **directory_scanner_nodes,
    **directory_auto_iterator_nodes,
    **ollama_nodes,
    **sound_notifier_nodes,
    **display_anything_nodes,
    **conditional_validator_nodes,
    **number_randomizer_nodes,
    **latent_upscaler_nodes,
    **llm_image_refine_nodes,
    **vae_decode_preview_nodes,
    **lazy_conditional_switch_nodes,
    **mask_combiner_nodes
}

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    **save_image_display,
    **metadata_display,
    **wildcard_display,
    **latent_generator_display,
    **directory_scanner_display,
    **directory_auto_iterator_display,
    **ollama_display,
    **sound_notifier_display,
    **display_anything_display,
    **conditional_validator_display,
    **number_randomizer_display,
    **latent_upscaler_display,
    **llm_image_refine_display,
    **vae_decode_preview_display,
    **lazy_conditional_switch_display,
    **mask_combiner_display
}

# Add the directory to the web (i.e client, i.e. javascript) extensions
nodes.EXTENSION_WEB_DIRS["Basify"] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'js')  # type: ignore[index]

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']