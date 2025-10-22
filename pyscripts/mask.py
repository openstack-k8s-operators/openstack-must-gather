#!/usr/libexec/platform-python

import json
import yaml
import base64
from binascii import Error as binascii_error
import argparse
import re
import os
import sys
from typing import Dict, Optional, Any, Union

# The following protect|connection keys have been collected from SoS project
# https://github.com/sosreport/sos/blob/main/sos/report/plugins/openstack_*.py
PROTECT_KEYS = [
    "username", "password", "default_user", "default_pass", "olmCAKey",
    "transport_url", "connection", "APIDatabasePassword",
    "CellDatabasePassword", "MetadataSecret", "ServicePassword",
    "CredentialKeys\\d", "FernetKeys\\d", "rabbit_password",
    "qpid_password", "nova_admin_password", "xenapi_connection_password",
    "server_auth", "admin_password", "metadata_proxy_shared_secret",
    "eapi_password", "crd_password", "primary_l3_host_password",
    "serverauth", "ucsm_password", "fixed_key", "ha_vrrp_auth_password",
    "ssl_key_password", "nsx_password", "vcenter_password",
    "edge_appliance_password", "tenant_admin_password", "apic_password",
    "memcache_secret_key", "connection_password", "host_password",
    "os_password", "readonly_user_password", "secret_key",
    "(tls|ca)\\.(key|crt)", "telemetry_secret", "metering_secret",
    "backup_tsm_password", "chap_password", "nas_password",
    "cisco_fc_fabric_password", "coraid_password", "eqlx_chap_password",
    "fc_fabric_password", "hitachi_auth_password", "hitachi_horcm_password",
    "hp3par_password", "hplefthand_password", "netapp_password",
    "netapp_sa_password", "nexenta_password", "san_password",
    "vmware_host_password", "zadara_password", "zfssa_initiator_password",
    "hmac_keys", "zfssa_target_password", "os_privileged_user_password",
    "ssl_client_key_password", "s3_store_secret_key",
    "vmware_server_password", "dns_passkey", "stack_domain_admin_password",
    "ldap_dns_password", "neutron_admin_password", "admin_token",
    "ca_password" "hdfs_ssh_pw", "maprfs_ssh_pw", "powervm_mgr_passwd",
    "virtual_power_host_pass", "vnc_password", "s3_secret_key",
    "ca_private_key_passphrase", "heartbeat_key", "DatabasePassword",
    "server_certs_key_passphrase", "ssh-privatekey",
]

CONNECTION_KEYS = ["rabbit", "database_connection",
                   "slave_connection", "sql_connection"]

# Error messages
ERR_STR = "Not a valid string for masking"
ERR_FORMAT = "Required a dict for masking"

# Masking string
MASK_STR = "**********"

# general and connection regexes are used to match the pattern that should be
# applied to both Protect keys and connection keys, which is the same thing
# done in SoS reports
gen_regex = r'(\w*(%s)\s*=\s*)(.*)' % "|".join(PROTECT_KEYS)
con_regex = r'((%s)\s*://)(\w*):(.*)(@(.*))' % "|".join(CONNECTION_KEYS)

# In k8s secrets, it's possible to define sensitive information in the form
# of <key> = <value> under the "Data" section. This kind of info is not matched
# within a config file, hence we need to parse keys and detect any potential
# data that matches the keys we want to protect/mask.
key_regex = r'(%s)$' % "|".join(PROTECT_KEYS)
conf_file_regex = r'(.*).(conf)$'
regexes = [gen_regex, con_regex]


# Custom YAML representer to preserve multi-line strings as block scalars
def str_representer(dumper: Any, data: str) -> Any:
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_representer)


class SecretMask():
    """
    Given a path to k8s secret containing sensitive base64 encoded data,
    this class implements the required functions to load, unpack the secret
    content, mask any potential sensitive data and pack it again.
    The resulting file won't expose any information that should be protected
    by the defined pattern.
    """

    def __init__(self, path: Optional[str] = None,
                 dump: bool = False) -> None:
        self.path: Union[str, None] = path
        self.dump: bool = dump

    def mask(self) -> bool:
        """
        Read a k8s secret dumped as yaml and process the
        Data section: for each entry analyze the resulting
        dict and mask any sensitive info if the pattern is
        matched.
        """
        s = self._readYaml()
        # s is None or empty dict, return
        if not s or len(s) == 0:
            return True

        # mask the dict containing k8s secret dump
        self._applyMask(s)

        # write the resulting, masked/encoded file
        self._writeYaml(dict(s))
        return True

    def _applyAnnotationsMask(self, annotations: Dict[str, Any]) -> Dict[str, Any]:
        last_config = annotations.get("kubectl.kubernetes.io/last-applied-configuration", None)
        if not last_config:
            return annotations
        try:
            last_applied_config = json.loads(last_config)

            # recursively mask secrets within last-applied-configuration
            self._applyMask(last_applied_config)
            annotations["kubectl.kubernetes.io/last-applied-configuration"] = json.dumps(last_applied_config, separators=(',', ':'))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error while parsing contents of kubectl.kubernetes.io/last-applied-configuration {e}")
            annotations["kubectl.kubernetes.io/last-applied-configuration"] = MASK_STR
        return annotations

    def _applyMask(self, s: Dict) -> None:
        for k, v in s.items():
            # if we have items in the loaded dict,
            # we look for the data section, which
            # is where we want to apply masking
            # now we also look for the metadata
            # section as it also contains secrets
            # within last-applied-configuration
            if k == "data":
                data = self._process_data(v)
                s[k] = data
            elif k == "metadata" and "annotations" in s[k]:
                s[k]["annotations"] = self._applyAnnotationsMask(s[k]["annotations"])

    def _readYaml(self) -> Dict[str, str]:
        """
        Read and Load the k8s Secret dumped as
        yaml file.
        """
        s = dict()
        try:
            assert self.path is not None
            with open(self.path, 'r') as f:
                s = yaml.safe_load(f)
            return s
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"Error while reading YAML: {e}")
            sys.exit(-1)
        return s

    def _writeYaml(self, encoded_secret: Any) -> None:
        """
        Re-write the masked secret in the same
        path.
        """
        try:
            assert self.path is not None
            with open(self.path, 'w') as f:
                yaml.safe_dump(encoded_secret, f,
                               default_flow_style=False)
        except (IOError, yaml.YAMLError) as e:
            print(f"Error while writing the masked file: {e}")

    def _writeFile(self, path: str, encoded_secret: Any) -> None:
        """
        Dump the masked secret containing a config file to a given
        path.
        """
        try:
            assert path is not None
            with open(path, 'w') as f:
                f.write(encoded_secret)
        except IOError as e:
            print(f"Error while writing the masked file: {e}")

    def _apply_regex(self, decoded_secret: str) -> str:
        """
        For each decoded_secret passed as argument, try
        to match the pattern according to the provided
        regexes and mask any potential sensitive info.
        """
        for pattern in regexes:
            decoded_secret = re.sub(pattern, r"\1{}".format(MASK_STR),
                                    decoded_secret, flags=re.I)
        return decoded_secret

    def _process_data(self, data_map: Any) -> Any:
        """
        Analyze the data_map dictionary passed as argument.
        If values are provided in the form:
        <key>=<value>
        we need to match the key and figure out if its value
        represents a sensitive data; if the secret content is
        provided in the form:
        <config_file>=<content>,
        we need instead to parse this content and matches the
        pattern in the content itself.
        """
        if not isinstance(data_map, dict):
            print(f"Error while masking file: {self.path}")
            return ERR_FORMAT

        d = dict()  # type: Dict[str, Any]
        for k, v in data_map.items():
            if len(v) == 0:
                # let's preserve entries without any b64
                # encoded string associated
                d[k] = ''
                continue
            # try to match the keys we want to protect in the dict
            if re.findall(key_regex, k):
                # mask the value of the key entirely
                masked = MASK_STR
            else:
                try:
                    masked = self._apply_regex(base64.b64decode(v).decode())
                    if self.dump and re.search(conf_file_regex, k):
                        self._writeFile('{}-{}'.format(self.path, k), masked)
                except (binascii_error, UnicodeDecodeError):
                    print(f"Error while masking key: {k}, for file: {self.path}")
                    d[k] = ERR_STR
                    continue
            # re-encode the entry
            d[k] = base64.b64encode(masked.encode()).decode()
        return d


class PlaintextMask():
    """
    Mask sensitive data in plain text YAML files (ConfigMaps and CRs).
    Unlike SecretMask, this works on non-base64 encoded data.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self.path: Union[str, None] = path

    def mask(self) -> bool:
        """
        Read a k8s resource (ConfigMap or CR) dumped as yaml and process
        recursively to mask any sensitive information.
        """
        resource = self._readYaml()
        if not resource or len(resource) == 0:
            return True

        # Recursively mask the entire resource
        self._applyMaskRecursive(resource)

        # Write the masked file
        self._writeYaml(resource)
        return True

    def _readYaml(self) -> Dict[str, Any]:
        """
        Read and Load the k8s resource dumped as yaml file.
        """
        try:
            assert self.path is not None
            with open(self.path, 'r') as f:
                resource = yaml.safe_load(f)
            return resource if resource else {}
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"Error while reading YAML {self.path}: {e}")
            return {}

    def _writeYaml(self, resource: Any) -> None:
        """
        Re-write the masked resource to the same path.
        """
        try:
            assert self.path is not None
            with open(self.path, 'w') as f:
                # Write with settings to preserve readability
                yaml.dump(resource, f, default_flow_style=False,
                          allow_unicode=True, sort_keys=False)
        except (IOError, yaml.YAMLError) as e:
            print(f"Error while writing the masked file {self.path}: {e}")

    def _applyMaskRecursive(self, obj: Any) -> Any:
        """
        Recursively traverse the object and mask sensitive data.
        Two-step strategy:
        1. If key name is sensitive AND value is single-line -> fully mask
        2. If multi-line (has newlines) -> parse content with regex
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    # If key name matches sensitive pattern and value is single-line, fully mask
                    # This catches: password: secret123, transport_url: mysql://..., etc.
                    if re.search(key_regex, key) and '\n' not in value:
                        obj[key] = MASK_STR
                    else:
                        # Parse content to mask sensitive parts
                        # This handles: customServiceConfig blocks (multi-line), long configs, etc.
                        obj[key] = self._applyRegex(value)
                elif isinstance(value, (dict, list)):
                    # Recursively process nested structures
                    self._applyMaskRecursive(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    obj[i] = self._applyRegex(item)
                elif isinstance(item, (dict, list)):
                    self._applyMaskRecursive(item)
        return obj

    def _applyRegex(self, text: str) -> str:
        """
        Apply regex patterns to mask sensitive information in text.
        Handles both single-line and multi-line strings.
        """
        for pattern in regexes:
            text = re.sub(pattern, r"\1{}".format(MASK_STR), text, flags=re.MULTILINE)
        return text


def get_resource_kind(path: str) -> Optional[str]:
    """
    Read a YAML file and return its 'kind' field to determine resource type.
    Returns None if the file cannot be read or doesn't have a 'kind' field.
    """
    try:
        with open(path, 'r') as f:
            resource = yaml.safe_load(f)
            if isinstance(resource, dict):
                return resource.get('kind', None)
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error while reading YAML to determine kind: {e}")
    return None


def mask_resource(path: str, dump_conf: bool = False) -> bool:
    """
    Dispatcher function that determines the resource type and applies
    the appropriate masking strategy:
    - Secrets: Use SecretMask (base64 decode/encode)
    - ConfigMaps/CRs/Other: Use PlaintextMask (direct text masking)
    """
    kind = get_resource_kind(path)

    if kind == "Secret":
        return SecretMask(path, dump_conf).mask()
    else:
        # ConfigMaps, CRs, and any other resource type
        return PlaintextMask(path).mask()


def parse_opts(argv: Any) -> Any:
    """
    Utility for the main function: it provides a way to parse
    options and return the arguments.
    """
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument('-p', '--path', metavar='PATH',
                        help="Path of the file where the masking \
                        should be applied")
    parser.add_argument('-d', '--dir', metavar='DIR_PATH',
                        help="Path of the directory where the masking \
                        should be applied")
    parser.add_argument('--dump-conf', action='store_true',
                        help="Dump the config files retrieved for a given \
                        service")
    opts = parser.parse_args(argv[1:])
    return opts


if __name__ == '__main__':
    # parse the provided options
    OPTS = parse_opts(sys.argv)

    if OPTS.dir is not None and os.path.exists(OPTS.dir):
        # reset OPTS.path in case it has been passed as
        # argument and process all the files found in
        # that directory
        for root, subdirs, files in os.walk(OPTS.dir):
            for f in files:
                # Skip non-YAML files
                if not f.endswith('.yaml') and not f.endswith('.yml'):
                    continue
                file_path = os.path.join(root, f)
                mask_resource(file_path, OPTS.dump_conf)

    if OPTS.path is not None and os.path.exists(OPTS.path):
        mask_resource(OPTS.path, OPTS.dump_conf)
