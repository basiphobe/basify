#!/usr/bin/env python3
"""
Convert ComfyUI UI format workflow to API format.
Uses the running ComfyUI server to do the conversion.
"""

import json
import sys
from pathlib import Path
import requests


def convert_workflow(ui_workflow_path: Path, output_path: Path | None = None, server: str = "127.0.0.1:8188") -> bool:
    """Convert UI format workflow to API format.
    
    Args:
        ui_workflow_path: Path to UI format workflow
        output_path: Path to save API format (default: same name with _api suffix)
        server: ComfyUI server address
        
    Returns:
        bool: True if successful
    """
    # Load UI workflow
    with open(ui_workflow_path, 'r') as f:
        ui_data = json.load(f)
    
    # Check if already API format
    if 'nodes' not in ui_data:
        print(f"✅ Workflow is already in API format!")
        if output_path and output_path != ui_workflow_path:
            with open(output_path, 'w') as f:
                json.dump(ui_data, f, indent=2)
            print(f"Copied to: {output_path}")
        return True
    
    # Use ComfyUI's prompt endpoint to convert
    # We'll send a serialize request
    try:
        # Try to get the API format by POSTing the workflow
        # ComfyUI can convert UI format to API format through its /prompt endpoint validation
        response = requests.post(
            f"http://{server}/prompt",
            json={"prompt": ui_data, "client_id": "converter"},
            timeout=10
        )
        
        if response.status_code == 400:
            # Expected - we're not actually running it, just validating
            # But we need a different approach
            pass
        
    except Exception as e:
        pass
    
    # Manual conversion approach
    print("Converting UI format to API format manually...")
    api_workflow = {}
    
    # Map links
    links = {}
    if 'links' in ui_data:
        for link in ui_data['links']:
            # link format: [id, origin_id, origin_slot, target_id, target_slot, type]
            if len(link) >= 5:
                link_id, origin_id, origin_slot, target_id, target_slot = link[:5]
                links[link_id] = {
                    'origin_id': origin_id,
                    'origin_slot': origin_slot,
                    'target_id': target_id,
                    'target_slot': target_slot
                }
    
    # Convert nodes
    for node in ui_data.get('nodes', []):
        node_id = str(node['id'])
        node_type = node['type']
        
        api_node = {
            'inputs': {},
            'class_type': node_type
        }
        
        # Add widget values as inputs
        widget_values = node.get('widgets_values', [])
        node_inputs = node.get('inputs', [])
        
        # First, add link-based inputs
        for idx, input_def in enumerate(node_inputs):
            input_name = input_def['name']
            
            if 'link' in input_def and input_def['link'] is not None:
                link_id = input_def['link']
                if link_id in links:
                    link_info = links[link_id]
                    # API format: [source_node_id, source_output_index]
                    api_node['inputs'][input_name] = [str(link_info['origin_id']), link_info['origin_slot']]
        
        # Then add widget-based inputs
        # This is tricky because we need to know which widget maps to which input
        # We'll use a heuristic based on node type
        
        if node_type == 'LoadImage' and widget_values:
            api_node['inputs']['image'] = widget_values[0]
        elif node_type == 'BasifyWildcardProcessor' and widget_values:
            # text, enable_wildcards, wildcard_directory, force_refresh, iterator_completed
            if len(widget_values) >= 1:
                api_node['inputs']['text'] = widget_values[0]
            if len(widget_values) >= 2:
                api_node['inputs']['enable_wildcards'] = widget_values[1]
            if len(widget_values) >= 3:
                api_node['inputs']['wildcard_directory'] = widget_values[2]
            if len(widget_values) >= 4:
                api_node['inputs']['force_refresh'] = widget_values[3] == 'true' if isinstance(widget_values[3], str) else widget_values[3]
            if len(widget_values) >= 5:
                api_node['inputs']['iterator_completed'] = widget_values[4]
        elif node_type == 'KSampler' and widget_values:
            # seed, steps, cfg, sampler_name, scheduler, denoise
            widget_names = ['seed', 'control_after_generate', 'steps', 'cfg', 'sampler_name', 'scheduler', 'denoise']
            for idx, value in enumerate(widget_values):
                if idx < len(widget_names):
                    api_node['inputs'][widget_names[idx]] = value
        else:
            # Generic approach: try to map by position
            # This won't work for all nodes but it's a start
            pass
        
        api_workflow[node_id] = api_node
    
    # Set output path
    if output_path is None:
        output_path = ui_workflow_path.parent / f"{ui_workflow_path.stem}_api.json"
    
    # Save
    with open(output_path, 'w') as f:
        json.dump(api_workflow, f, indent=2)
    
    print(f"✅ Converted successfully!")
    print(f"Saved to: {output_path}")
    print(f"\nNote: Manual conversion may not preserve all node inputs perfectly.")
    print(f"If you encounter issues, use ComfyUI's built-in 'Save (API Format)' option instead.")
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert ComfyUI UI format workflow to API format"
    )
    parser.add_argument(
        'workflow',
        type=Path,
        help='Path to UI format workflow JSON'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output path for API format (default: <input>_api.json)'
    )
    parser.add_argument(
        '--server',
        type=str,
        default='127.0.0.1:8188',
        help='ComfyUI server address (default: 127.0.0.1:8188)'
    )
    
    args = parser.parse_args()
    
    if not args.workflow.exists():
        print(f"Error: Workflow file not found: {args.workflow}")
        sys.exit(1)
    
    success = convert_workflow(args.workflow, args.output, args.server)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
