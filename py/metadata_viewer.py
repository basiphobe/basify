import json
import logging

# Add Colors class at the top
class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)

class MetadataViewer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            # input_fields_group: Can be either required, hidden or optional.
            # A "node" class must have property `required`
            "required": {
                "image": ("IMAGE",)
            },
            "hidden": {
                "extra_pnginfo": "EXTRA_PNGINFO",
                "id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("metadata_json",)
    FUNCTION = "collect_metadata"
    CATEGORY = "basify"
    
    def collect_metadata(self, image, extra_pnginfo: dict, id: int):
        metadata = {"id": str(id)}
        
        # Add all contents from extra_pnginfo
        if extra_pnginfo:
            metadata.update(extra_pnginfo)

        # Parse workflow nodes with fallback
        workflow_data = metadata.get("workflow", {})
        nodes = self.parse_workflow_nodes(workflow_data) if workflow_data else {}
        
        # Create a simplified metadata structure specifically for display
        display_metadata = {
            "workflow_name": metadata.get("prompt", {}).get("name", "Unnamed Workflow"),
            "nodes": nodes
        }
        
        # Return properly formatted JSON string that will work with metadata embedding
        return (json.dumps(display_metadata, indent=None, ensure_ascii=False),)

    def parse_workflow_nodes(self, workflow_json):
        try:
            # Convert string to JSON if needed
            if isinstance(workflow_json, str):
                workflow_data = json.loads(workflow_json)
            else:
                workflow_data = workflow_json

            # Get the nodes list from workflow
            nodes = workflow_data.get("nodes", [])
            if not nodes:
                return {}
            
            # Sort nodes by order value
            sorted_nodes = sorted(nodes, key=lambda x: x.get("order", 0))
            
            # Create result dictionary
            result = {}
            
            # Process each node
            for node in sorted_nodes:
                node_title = node.get("title") or node.get("type")
                
                # Skip ShowText nodes
                if node_title and "ShowText|" in str(node_title):
                    continue
                
                # Get and filter widget values
                widgets_values = node.get("widgets_values", [])
                if widgets_values:
                    # Filter out None and empty string values, convert to strings
                    filtered_values = [
                        str(val) for val in widgets_values 
                        if val is not None and str(val).strip()
                    ]
                    
                    # Only include nodes with non-empty filtered values
                    if filtered_values and node_title and node_title not in result:
                        result[node_title] = filtered_values
            
            return result

        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.error(f"{Colors.RED}[BASIFY] Error parsing workflow: {e}{Colors.ENDC}")
            return {}
        except Exception as e:
            logger.error(f"{Colors.RED}[BASIFY] Unexpected error parsing workflow: {e}{Colors.ENDC}")
            return {}

NODE_CLASS_MAPPINGS = {
    "BasifyMetadataViewer": MetadataViewer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasifyMetadataViewer": "Basify: Metadata Viewer"
}
