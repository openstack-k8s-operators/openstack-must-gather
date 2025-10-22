#!/usr/bin/python

import unittest
import os
import yaml
import tempfile
import shutil
from mask import PlaintextMask

# sample directory used to load yaml files
SAMPLE_DIR = "tests/samples_plaintext"


class TestPlaintextMask(unittest.TestCase):
    """
    The class that implements basic tests for
    PlaintextMask.
    """

    def setUp(self):
        """
        Set up temporary directory for test files
        """
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """
        Clean up temporary directory
        """
        shutil.rmtree(self.temp_dir)

    def _read_sample(self, path):
        """
        utility function to load a sample yaml file.
        """
        with open(path, 'r') as f:
            s = yaml.safe_load(f)
        return s

    def _create_temp_file(self, content):
        """
        Create a temporary test file and return its path
        """
        temp_file = os.path.join(self.temp_dir, 'test.yaml')
        with open(temp_file, 'w') as f:
            yaml.dump(content, f)
        return temp_file

    def test_mask_configmap_with_sensitive_data(self):
        """
        Test that ConfigMaps with sensitive data are properly masked
        """
        configmap = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {'name': 'test-config'},
            'data': {
                'password': 'secretpass123',
                'config.conf': '[database]\nconnection = mysql://user:pass@localhost/db\nusername = dbuser\npassword = dbpass'
            }
        }
        temp_file = self._create_temp_file(configmap)

        # Apply masking
        PlaintextMask(temp_file).mask()

        # Read masked result
        result = self._read_sample(temp_file)

        # Assert password field is fully masked
        self.assertEqual(result['data']['password'], '**********')

        # Assert config content has sensitive values masked
        config_content = result['data']['config.conf']
        self.assertIn('connection = **********', config_content)
        self.assertIn('username = **********', config_content)
        self.assertIn('password = **********', config_content)
        self.assertNotIn('secretpass123', str(result))
        self.assertNotIn('dbpass', config_content)

    def test_mask_cr_with_customserviceconfig(self):
        """
        Test that CRs with customServiceConfig are properly masked
        """
        cr = {
            'apiVersion': 'core.openstack.org/v1beta1',
            'kind': 'OpenStackControlPlane',
            'metadata': {'name': 'test'},
            'spec': {
                'cinder': {
                    'template': {
                        'cinderVolumes': {
                            'volume1': {
                                'customServiceConfig': '[tripleo_hpe_3par_csi]\nhpe3par_username=edit3par\nhpe3par_password=3parpass'
                            }
                        }
                    }
                }
            }
        }
        temp_file = self._create_temp_file(cr)

        # Apply masking
        PlaintextMask(temp_file).mask()

        # Read masked result
        result = self._read_sample(temp_file)

        # Get the customServiceConfig value
        config = result['spec']['cinder']['template']['cinderVolumes']['volume1']['customServiceConfig']

        # Assert sensitive values are masked but structure preserved
        self.assertIn('hpe3par_username=**********', config)
        self.assertIn('hpe3par_password=**********', config)
        self.assertNotIn('edit3par', config)
        self.assertNotIn('3parpass', config)

    def test_mask_connection_strings(self):
        """
        Test that connection strings are properly masked
        """
        configmap = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'data': {
                'transport_url': 'rabbit://guest:guestpass123@rabbitmq:5672/',
                'database_connection': 'mysql://dbuser:dbpass456@localhost/keystone'
            }
        }
        temp_file = self._create_temp_file(configmap)

        # Apply masking
        PlaintextMask(temp_file).mask()

        # Read masked result
        result = self._read_sample(temp_file)

        # Assert credentials are masked (may be fully masked or partially masked)
        self.assertNotIn('guestpass123', result['data']['transport_url'])
        self.assertNotIn('dbpass456', result['data']['database_connection'])
        # Verify something was masked
        self.assertIn('**********', str(result['data']))

    def test_no_masking_for_clean_data(self):
        """
        Test that data without sensitive information is not changed
        """
        configmap = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'data': {
                'regular_key': 'regular_value',
                'config': '[DEFAULT]\ndebug = true\nlog_level = INFO'
            }
        }
        temp_file = self._create_temp_file(configmap)
        original = self._read_sample(temp_file)

        # Apply masking
        PlaintextMask(temp_file).mask()

        # Read masked result
        result = self._read_sample(temp_file)

        # Assert non-sensitive data is unchanged
        self.assertEqual(result['data']['regular_key'], original['data']['regular_key'])
        self.assertIn('debug = true', result['data']['config'])
        self.assertIn('log_level = INFO', result['data']['config'])

    def test_multiline_preservation(self):
        """
        Test that multi-line strings are preserved without extra blank lines
        """
        configmap = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'data': {
                'config': 'line1\nline2\npassword=secret\nline4'
            }
        }
        temp_file = self._create_temp_file(configmap)

        # Apply masking
        PlaintextMask(temp_file).mask()

        # Read masked result
        result = self._read_sample(temp_file)
        config = result['data']['config']

        # Count newlines - should not have doubled
        original_lines = configmap['data']['config'].count('\n')
        result_lines = config.count('\n')
        self.assertEqual(original_lines, result_lines)

        # Assert password is masked
        self.assertIn('password=**********', config)

    def test_nested_structure_masking(self):
        """
        Test that nested structures are properly traversed and masked
        """
        cr = {
            'spec': {
                'level1': {
                    'level2': {
                        'level3': {
                            'password': 'deeppass123',
                            'config': 'admin_password=adminpass'
                        }
                    }
                }
            }
        }
        temp_file = self._create_temp_file(cr)

        # Apply masking
        PlaintextMask(temp_file).mask()

        # Read masked result
        result = self._read_sample(temp_file)

        # Assert deeply nested values are masked
        level3 = result['spec']['level1']['level2']['level3']
        self.assertEqual(level3['password'], '**********')
        self.assertIn('admin_password=**********', level3['config'])
        self.assertNotIn('deeppass123', str(result))
        self.assertNotIn('adminpass', str(result))

    def test_sample_files(self):
        """
        Test masking on sample files in tests/samples_plaintext directory
        """
        if not os.path.exists(SAMPLE_DIR):
            self.skipTest(f"Sample directory {SAMPLE_DIR} does not exist")
            return

        for root, subdirs, files in os.walk(SAMPLE_DIR):
            for f in files:
                if not f.endswith('.yaml'):
                    continue

                print(f"Processing file {f}")
                sample_path = os.path.join(root, f)

                # Copy to temp location
                temp_file = os.path.join(self.temp_dir, f)
                shutil.copy(sample_path, temp_file)

                original = self._read_sample(temp_file)

                # Apply masking
                PlaintextMask(temp_file).mask()

                result = self._read_sample(temp_file)

                # Files with 'nochange' should remain the same
                if "nochange" in f:
                    self.assertEqual(original, result,
                                     f"File {f} should not be changed")
                else:
                    # Files with sensitive data should be different
                    self.assertNotEqual(original, result,
                                        f"File {f} should be masked")


if __name__ == '__main__':
    unittest.main()
