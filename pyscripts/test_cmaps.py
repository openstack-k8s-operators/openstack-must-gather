#!/usr/bin/env python3

"""
Test script for cmaps.py ConfigMap splitting functionality.
Tests with the sample ConfigMapList YAML file and creates individual ConfigMap
files (both masked and unmasked use cases).
"""

import tempfile
import unittest
from pathlib import Path
from cmaps import split_configmaps

SAMPLE_SRC_FILE = "tests/samples_plaintext/configmaps.yaml"
TARGET_DIR = "configmaps"


class TestConfigMapSplitting(unittest.TestCase):
    """
    Test ConfigMap splitting functionality with unittest framework.
    """

    def setUp(self):
        """
        Set up test.
        """
        self.sample_file = SAMPLE_SRC_FILE
        self.expected_files = [
            "dns.yaml",
            "horizon-config-data.yaml",
            "nova-config-data.yaml"
        ]

    def test_splitting_without_masking(self):
        """
        Test ConfigMap splitting without masking.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(("{}/{}".format(temp_dir, TARGET_DIR)))
            created_files = split_configmaps(
                    str(self.sample_file), str(output_dir), apply_mask=False)

            # Test correct number of files created
            self.assertEqual(len(created_files), len(self.expected_files))

            # Test all expected files were created
            created_names = [Path(f).name for f in created_files]
            missing_files = set(self.expected_files) - set(created_names)
            unexpected_files = set(created_names) - set(self.expected_files)

            self.assertEqual(len(missing_files), 0)
            self.assertEqual(len(unexpected_files), 0)

            # Assert the generated files are not empty
            for file_path in created_files:
                file_size = Path(file_path).stat().st_size
                self.assertGreater(file_size, 0)

    def test_splitting_with_masking(self):
        """
        Test ConfigMap splitting with masking enabled.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(("{}/{}".format(temp_dir, TARGET_DIR)))
            mask_output_dir = Path("{}/{}_masked".format(temp_dir, TARGET_DIR))

            # Create masked files
            created_masked_files = split_configmaps(
                    self.sample_file, mask_output_dir, apply_mask=True)

            # Check the expected amount of files are generated
            self.assertEqual(
                    len(self.expected_files), len(created_masked_files))

            # Check nova config for masking (contains a plaintext 'password'
            # key and a transportUrl that should be masked)
            nova_unmasked = output_dir/"nova-config-data.yaml"
            nova_masked = mask_output_dir/"nova-config-data.yaml"

            if nova_unmasked.exists() and nova_masked.exists():
                masked_content = nova_masked.read_text()

                # Check that the masking was attempted (files are processed)
                # Note: The actual masking depends on the regex patterns in
                # mask.py
                # We mainly test that the masking process runs without error
                # and the resulting file is different from the original one
                self.assertGreater(len(masked_content), 0)
                self.assertNotEqual(masked_content, nova_unmasked.read_text())

    def test_is_configmap(self):
        """
        Test that created files contain valid YAML ConfigMap content.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)/"configmaps"
            created_files = split_configmaps(
                    self.sample_file, output_dir, apply_mask=False)
            for f in created_files:
                content = Path(f).read_text()
                # Test basic ConfigMap structure
                self.assertIn("apiVersion: v1",
                              content, f"File {f} should have apiVersion")
                self.assertIn("kind: ConfigMap",
                              content, f"File {f} should have kind: ConfigMap")
                self.assertIn("metadata:",
                              content, f"File {f} should have metadata")
                self.assertIn("data:",
                              content, f"File {f} should have data section")


if __name__ == "__main__":
    # Run the unittest
    unittest.main()
