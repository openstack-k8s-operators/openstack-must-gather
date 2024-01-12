#!/usr/bin/python

import unittest
import os
import yaml
from mask import SecretMask

# sample directory used to load yaml files
SAMPLE_DIR = "tests/samples"


class TestSecretMask(unittest.TestCase):
    """
    The class that implements basic tests for
    SecretMask.
    """

    def _read_sample(self, path):
        """
        utility function to load a sample yaml file.
        """
        with open(path, 'r') as f:
            s = yaml.safe_load(f)
        return s

    def test_mask(self):
        """
        For each file present in the tests/samples we:
        - Load the file by reading the yaml definition
        - Process using the SecreMask module
        - assert the 'data' content of the secret is
          different
        """
        for root, subdirs, files in os.walk(SAMPLE_DIR):
            for f in files:
                print("Processing file %s" % f)
                actual = self._read_sample(os.path.join(root, f))
                # Mask secret by processing the data section
                # of the yaml file we got
                s = SecretMask(os.path.join(root, f), False)
                expected = s._process_data(actual['data'])
                """
                files are named secret{1, 2, 3, ... N}: for these secrets
                we expect a change in their 'data' content because sensitive
                data has been masked; the sample file named "nochange.yaml",
                instead, is the one that does not contain any sensitive data,
                hence no masking is applied and we expect the original data
                content being the same as the processed one.
                """
                if "nochange" in f:
                    # the b64 encoded entry should be the same
                    # as we haven't applied any masking to this
                    # file
                    self.assertEqual(actual['data'], expected)
                else:
                    # The b64 encoded entry should be different
                    self.assertNotEqual(actual['data'], expected)


if __name__ == '__main__':
    unittest.main()
