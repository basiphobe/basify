#!/usr/bin/env python3
"""
Batch Image Processor for ComfyUI
Processes multiple images through a ComfyUI workflow by queuing them one at a time.
"""

import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any
import requests
import websocket


class ComfyUIBatchProcessor:
    """Process images through ComfyUI workflow with external iteration control."""
    
    def __init__(self, server_address: str = "127.0.0.1:8188"):
        """Initialize the batch processor.
        
        Args:
            server_address: ComfyUI server address (default: 127.0.0.1:8188)
        """
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        
    def queue_prompt(self, prompt: dict[str, Any]) -> str | None:
        """Queue a prompt for execution.
        
        Args:
            prompt: The workflow prompt dictionary
            
        Returns:
            str: Prompt ID if successful, None otherwise
        """
        p = {"prompt": prompt, "client_id": self.client_id}
        
        try:
            response = requests.post(
                f"http://{self.server_address}/prompt",
                json=p,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result.get('prompt_id')
        except requests.exceptions.HTTPError as e:
            # Try to get the error details from the response
            try:
                error_details = response.json()
                print(f"Error queuing prompt: {e}")
                if 'error' in error_details:
                    print(f"  Details: {error_details['error']}")
                if 'node_errors' in error_details:
                    print(f"  Node errors: {error_details['node_errors']}")
            except:
                print(f"Error queuing prompt: {e}")
            return None
        except Exception as e:
            print(f"Error queuing prompt: {e}")
            return None
    
    def get_history(self, prompt_id: str) -> dict[str, Any] | None:
        """Get execution history for a prompt.
        
        Args:
            prompt_id: The prompt ID to check
            
        Returns:
            dict: History data if available, None otherwise
        """
        try:
            response = requests.get(
                f"http://{self.server_address}/history/{prompt_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting history: {e}")
            return None
    
    def upload_image(self, image_path: Path) -> dict[str, Any] | None:
        """Upload an image to ComfyUI.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            dict: Upload result with 'name' and 'subfolder', or None if failed
        """
        try:
            with open(image_path, 'rb') as f:
                files = {'image': (image_path.name, f, 'image/png')}
                data = {'overwrite': 'true'}
                
                response = requests.post(
                    f"http://{self.server_address}/upload/image",
                    files=files,
                    data=data,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error uploading image {image_path}: {e}")
            return None
    
    def wait_for_completion(self, prompt_id: str, timeout: int = 0) -> bool:
        """Wait for a prompt to complete execution.
        
        Args:
            prompt_id: The prompt ID to wait for
            timeout: Maximum time to wait in seconds (0 = no timeout, wait indefinitely)
            
        Returns:
            bool: True if completed successfully, False if timeout or error
        """
        start_time = time.time()
        
        while True:
            # Check timeout only if it's set (> 0)
            if timeout > 0 and (time.time() - start_time) >= timeout:
                print(f"Timeout waiting for prompt {prompt_id}")
                return False
            
            history = self.get_history(prompt_id)
            
            if history and prompt_id in history:
                # Prompt has completed
                prompt_history = history[prompt_id]
                if 'outputs' in prompt_history:
                    return True
            
            time.sleep(0.5)
    
    def _ui_to_api(self, ui_data: dict[str, Any]) -> dict[str, Any]:
        """Convert UI format workflow to API format.
        
        Args:
            ui_data: Workflow in UI format (browser save)
            
        Returns:
            API format workflow (flat node dict)
        """
        api_workflow = {}
        
        # Build link mapping: link_id -> {origin_id, origin_slot}
        link_map = {}
        for link in ui_data.get('links', []):
            if len(link) >= 6:
                link_id, origin_id, origin_slot, target_id, target_slot, link_type = link[:6]
                link_map[link_id] = {
                    'origin_id': str(origin_id),
                    'origin_slot': origin_slot
                }
        
        # Build node map and identify reroutes
        node_map = {}
        reroute_map = {}  # node_id -> input_link_id
        for node in ui_data.get('nodes', []):
            node_id = str(node['id'])
            node_map[node_id] = node
            
            # Track reroute nodes
            if node['type'] == 'Reroute':
                # Reroutes should have one input
                if node.get('inputs') and len(node['inputs']) > 0:
                    input_link = node['inputs'][0].get('link')
                    if input_link:
                        reroute_map[node_id] = input_link
        
        # Resolve reroutes: trace back to the original source
        def resolve_link(link_id, visited=None):
            if visited is None:
                visited = set()
            
            if link_id in visited:
                return None  # Circular reference, shouldn't happen
            visited.add(link_id)
            
            if link_id not in link_map:
                return None
            
            link_info = link_map[link_id]
            origin_id = link_info['origin_id']
            
            # If origin is a reroute, trace through it
            if origin_id in reroute_map:
                upstream_link = reroute_map[origin_id]
                return resolve_link(upstream_link, visited)
            
            return link_info
        
        # Convert each node (skip reroutes)
        for node in ui_data.get('nodes', []):
            node_id = str(node['id'])
            node_type = node['type']
            
            # Skip reroute nodes - they're handled via link resolution
            if node_type == 'Reroute':
                continue
            
            api_node = {
                'inputs': {},
                'class_type': node_type
            }
            
            # Process inputs: first links, then widgets
            node_inputs = node.get('inputs', [])
            widget_values = node.get('widgets_values', [])
            
            # Track which inputs are from links vs widgets
            widget_index = 0
            
            for input_def in node_inputs:
                input_name = input_def['name']
                
                # Check if this input is connected via link
                if 'link' in input_def and input_def['link'] is not None:
                    link_id = input_def['link']
                    # Resolve through reroutes
                    link_info = resolve_link(link_id)
                    if link_info:
                        # API format: [source_node_id_str, source_output_slot_int]
                        api_node['inputs'][input_name] = [
                            link_info['origin_id'],
                            link_info['origin_slot']
                        ]
                else:
                    # This input comes from a widget
                    # Check if there's a widget for this input
                    if 'widget' in input_def and widget_index < len(widget_values):
                        api_node['inputs'][input_name] = widget_values[widget_index]
                        widget_index += 1
            
            # Handle remaining widget values (widgets without explicit input definitions)
            # This happens for nodes where widgets don't have link options
            while widget_index < len(widget_values):
                # We skip these for now
                widget_index += 1
            
            api_workflow[node_id] = api_node
        
        return api_workflow
    
    def process_images(
        self,
        workflow_path: Path,
        image_dir: Path,
        image_node_id: str,
        extensions: list[str] | None = None,
        timeout: int = 0
    ) -> None:
        """Process all images in a directory through the workflow.
        
        Args:
            workflow_path: Path to the workflow JSON file
            image_dir: Directory containing images to process
            image_node_id: ID of the LoadImage node in the workflow
            extensions: List of image extensions to process (default: common formats)
            timeout: Timeout per image in seconds (0 = no timeout, wait indefinitely)
        """
        if extensions is None:
            extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']
        
        # Load workflow
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
        
        # Convert UI format to API format if needed
        if 'nodes' in workflow_data:
            print("Converting UI format to API format...")
            workflow = self._ui_to_api(workflow_data)
        else:
            workflow = workflow_data
        
        # Get list of images
        images = []
        for ext in extensions:
            images.extend(list(image_dir.glob(f'*{ext}')))
            images.extend(list(image_dir.glob(f'*{ext.upper()}')))
        
        images = sorted(set(images))
        
        if not images:
            print(f"No images found in {image_dir}")
            return
        
        print(f"Found {len(images)} images to process")
        
        # Process each image
        for idx, image_path in enumerate(images, 1):
            print(f"\n[{idx}/{len(images)}] Processing: {image_path.name}")
            
            # Upload image to ComfyUI
            upload_result = self.upload_image(image_path)
            if not upload_result:
                print(f"  ❌ Failed to upload image, skipping")
                continue
            
            # Update workflow with uploaded image
            if image_node_id not in workflow:
                print(f"  ❌ Image node ID '{image_node_id}' not found in workflow")
                continue
            
            workflow[image_node_id]['inputs']['image'] = upload_result['name']
            if 'subfolder' in upload_result:
                workflow[image_node_id]['inputs']['subfolder'] = upload_result.get('subfolder', '')
            
            # Queue the prompt
            prompt_id = self.queue_prompt(workflow)
            if not prompt_id:
                print(f"  ❌ Failed to queue prompt, skipping")
                continue
            
            print(f"  📋 Queued with prompt ID: {prompt_id}")
            
            # Wait for completion
            if self.wait_for_completion(prompt_id, timeout=timeout):
                print(f"  ✅ Completed successfully")
            else:
                print(f"  ⚠️  Execution timed out or failed")
        
        print(f"\n🎉 Batch processing complete! Processed {len(images)} images.")


def main():
    """Main entry point for the batch processor."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Process multiple images through a ComfyUI workflow"
    )
    parser.add_argument(
        'workflow',
        type=Path,
        help='Path to the ComfyUI workflow JSON file'
    )
    parser.add_argument(
        'image_dir',
        type=Path,
        help='Directory containing images to process'
    )
    parser.add_argument(
        '--image-node-id',
        type=str,
        required=True,
        help='ID of the LoadImage node in the workflow (e.g., "1234")'
    )
    parser.add_argument(
        '--server',
        type=str,
        default='127.0.0.1:8188',
        help='ComfyUI server address (default: 127.0.0.1:8188)'
    )
    parser.add_argument(
        '--extensions',
        type=str,
        nargs='+',
        default=None,
        help='Image file extensions to process (default: common formats)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=0,
        help='Timeout per image in seconds (default: 0 = no timeout, wait indefinitely)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.workflow.exists():
        print(f"Error: Workflow file not found: {args.workflow}")
        sys.exit(1)
    
    if not args.image_dir.exists():
        print(f"Error: Image directory not found: {args.image_dir}")
        sys.exit(1)
    
    if not args.image_dir.is_dir():
        print(f"Error: {args.image_dir} is not a directory")
        sys.exit(1)
    
    # Process images
    processor = ComfyUIBatchProcessor(server_address=args.server)
    processor.process_images(
        workflow_path=args.workflow,
        image_dir=args.image_dir,
        image_node_id=args.image_node_id,
        extensions=args.extensions,
        timeout=args.timeout
    )


if __name__ == '__main__':
    main()
