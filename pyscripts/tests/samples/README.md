# Test Samples for mask.py (Secret Masking)

This directory contains test samples for validating Secret masking functionality.

## Test Files

### Valid Secrets (Should be Masked)

- **`secret1.yaml`**: Contains CredentialKeys and FernetKeys that should be fully masked
- **`secret2.yaml`**: Contains connection strings and passwords in config files
- **`secret3.yaml`**: Contains various sensitive fields

### Clean Data (No Masking Expected)

- **`nochange.yaml`**: Contains only non-sensitive configuration data. The test verifies that this file remains unchanged after masking.

### Error Handling Test Cases

These files intentionally contain malformed data to test error handling:

- **`secret4_no_dict.yaml`**: The `data` field is a string instead of a dictionary. Tests that the code handles malformed Secret structure gracefully.
  - **Expected behavior**: Error message printed, code continues without crashing

- **`secret5_no_utf-8_encoded.yaml`**: Contains invalid/incomplete base64 values in the `data` field (`"cmFi22"` and `"YW"`).
  - **Expected behavior**: Error messages printed for invalid keys, valid keys are processed normally

## Expected Test Output

During test execution, you will see error messages like:
```
Error while masking file: tests/samples/secret4_no_dict.yaml
Error while masking key: one, for file: tests/samples/secret5_no_utf-8_encoded.yaml
Error while masking key: two, for file: tests/samples/secret5_no_utf-8_encoded.yaml
```

**These error messages are expected and indicate proper error handling.** The test passes because the code gracefully handles these edge cases instead of crashing.

