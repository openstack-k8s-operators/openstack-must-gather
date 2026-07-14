#!/usr/bin/env python3

"""
Split a Kubernetes ConfigMapList YAML file into individual ConfigMap files.
Uses only Python standard library (no external dependencies).
Optionally applies masking to the split files.
"""

import yaml
import os
import sys
import argparse
from pathlib import Path

# Import mask module for applying masking
try:
    from mask import mask_data
except ImportError:
    mask_data = None


def split_configmaps(input_file, output_dir='configmaps', apply_mask=False):
    """
    Split a ConfigMapList YAML file into individual ConfigMap files.

    Args:
        input_file: Path to the input YAML file
        output_dir: Directory where individual files will be saved
        apply_mask: Whether to apply masking to the split files

    Returns:
        List of created file paths
    """

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Read and parse the YAML file
    with open(input_file, 'r') as f:
        data = yaml.safe_load(f)

    # Validate it's a ConfigMapList
    if data.get('kind') != 'ConfigMapList':
        print(f"Warn: Expected kind 'ConfigMapList', got '{data.get('kind')}'")
        return

    # Get the list of ConfigMaps
    configmaps = data.get('items', [])
    created_files = []

    total = len(configmaps)
    print(f"Processing {total} ConfigMaps from {input_file}", flush=True)

    # Process each ConfigMap
    for i, cm in enumerate(configmaps, 1):
        # Extract metadata
        metadata = cm.get('metadata', {})
        name = metadata.get('name', f'unnamed-{i}')

        # Create filename using configmap name
        filename = f"{name}.yaml"
        filepath = output_path / filename

        print(f"  [{i}/{total}] {name}", flush=True)

        if apply_mask and mask_data:
            try:
                mask_data(cm, str(filepath))
            except Exception as e:
                print(f"Warning: Could not mask {filepath}: {e}")
        elif apply_mask and not mask_data:
            print(f"Warning: Masking requested but mask module not available")
        else:
            with open(filepath, 'w') as f:
                yaml.dump(cm, f, default_flow_style=False, sort_keys=False)

        created_files.append(str(filepath))

    return created_files


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Split ConfigMapList YAML file into individual ConfigMaps'
    )
    parser.add_argument('input_file', help='Path to the input ConfigMapList YAML file')  # noqa E501
    parser.add_argument('output_dir', nargs='?', default='configmaps',
                        help='Directory where individual files will be saved (default: configmaps)')  # noqa E501
    parser.add_argument('--mask', action='store_true',
                        help='Apply masking to the split ConfigMap files')

    args = parser.parse_args()

    # Check input file
    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found")
        sys.exit(1)

    # Split the ConfigMapList into individual ConfigMaps
    try:
        split_configmaps(args.input_file, args.output_dir, args.mask)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
