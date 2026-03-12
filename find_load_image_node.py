#!/usr/bin/env python3
"""
Helper script to find LoadImage node IDs in a ComfyUI workflow.
"""

import json
import sys
from pathlib import Path


def find_load_image_nodes(workflow_path: Path) -> list[tuple[str, dict]]:
    """Find all LoadImage nodes in a workflow.
    
    Args:
        workflow_path: Path to workflow JSON
        
    Returns:
        List of (node_id, node_data) tuples
    """
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    load_image_nodes = []
    
    # Check if UI format (has 'nodes' array) or API format (direct node dict)
    if 'nodes' in workflow:
        # UI format
        for node in workflow['nodes']:
            if node.get('type') == 'LoadImage':
                node_id = str(node['id'])
                node_data = {
                    'id': node_id,
                    'type': node['type'],
                    'widgets_values': node.get('widgets_values', [])
                }
                load_image_nodes.append((node_id, node_data))
    else:
        # API format
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get('class_type') == 'LoadImage':
                load_image_nodes.append((node_id, node_data))
    
    return load_image_nodes


def main():
    if len(sys.argv) != 2:
        print("Usage: find_load_image_node.py <workflow.json>")
        sys.exit(1)
    
    workflow_path = Path(sys.argv[1])
    
    if not workflow_path.exists():
        print(f"Error: File not found: {workflow_path}")
        sys.exit(1)
    
    nodes = find_load_image_nodes(workflow_path)
    
    if not nodes:
        print("❌ No LoadImage nodes found in workflow")
        print("\nYou need to add a LoadImage node to your workflow.")
        sys.exit(1)
    
    print(f"✅ Found {len(nodes)} LoadImage node(s):\n")
    
    for node_id, node_data in nodes:
        # Get current image from either API or UI format
        if 'inputs' in node_data:
            # API format
            current_image = node_data.get('inputs', {}).get('image', 'none')
        else:
            # UI format
            widgets = node_data.get('widgets_values', [])
            current_image = widgets[0] if widgets else 'none'
        
        print(f"  Node ID: {node_id}")
        print(f"  Current image: {current_image}")
        print()
    
    if len(nodes) == 1:
        print(f"Use this in your batch command:")
        print(f"  --image-node-id {nodes[0][0]}")
    else:
        print("Multiple LoadImage nodes found. Choose the one you want to replace with batch images.")


if __name__ == '__main__':
    main()
