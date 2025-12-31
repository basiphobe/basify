import os
import nodes

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

# Import routes to register web endpoints (no exports needed)
from .py import routes  # noqa: F401

NODE_CLASS_MAPPINGS = {
    **save_image_nodes,
    **metadata_nodes,
    **wildcard_nodes,
    **latent_generator_nodes,
    **directory_scanner_nodes,
    **directory_auto_iterator_nodes,
    **ollama_nodes,
    **sound_notifier_nodes
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **save_image_display,
    **metadata_display,
    **wildcard_display,
    **latent_generator_display,
    **directory_scanner_display,
    **directory_auto_iterator_display,
    **ollama_display,
    **sound_notifier_display
}

# Add the directory to the web (i.e client, i.e. javascript) extensions
nodes.EXTENSION_WEB_DIRS["Basify"] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'js')

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']