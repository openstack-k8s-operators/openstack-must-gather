# Test Samples for mask.py (ConfigMap/CR Masking)

This directory contains test samples for validating plain text YAML resource masking (ConfigMaps and Custom Resources).

## Test Files

### ConfigMaps with Sensitive Data

- **`configmap1.yaml`**: Contains passwords, usernames, and connection strings that should be masked
  - Tests: password field masking, connection string masking, multi-line config parsing

- **`mixed_sensitive.yaml`**: Contains a mix of sensitive and non-sensitive data
  - Tests: Selective masking (only sensitive values masked, non-sensitive preserved)
  - Includes: transport_url, admin_token, config with passwords, regular values

### Custom Resources

- **`cr_customconfig.yaml`**: OpenStackControlPlane CR with `customServiceConfig` fields
  - Tests: Multi-line config parsing, masking within config blocks
  - Contains: HPE 3PAR credentials, LVM admin password

### Clean Data (No Masking Expected)

- **`nochange.yaml`**: Contains only non-sensitive configuration data
  - Tests: Verification that clean data remains unchanged
  - No passwords, credentials, or sensitive information

## What Gets Masked

The masking logic:

1. **Fully masked keys** (short values only):
   - `password`, `username`, `admin_token`, etc.
   - Example: `password: secret123` → `password: '**********'`

2. **Parsed content** (multi-line configs):
   - `customServiceConfig`, config files, etc.
   - Only sensitive lines are masked, structure preserved
   - Example:
     ```yaml
     config: |
       hpe3par_username=admin     →    hpe3par_username=**********
       hpe3par_password=pass123   →    hpe3par_password=**********
     ```

3. **Connection strings**:
   - Credentials in URLs are masked
   - Example: `mysql://user:pass@host` → `mysql://**********`

## Running Tests

```bash
cd pyscripts
python3 test_mask_plaintext.py
```

All tests should pass without error messages (unlike mask.py tests which have intentional error cases).

