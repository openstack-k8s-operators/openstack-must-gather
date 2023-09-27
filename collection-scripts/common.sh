#!/bin/bash

export BASE_COLLECTION_PATH="${BASE_COLLECTION_PATH:-/must-gather}"
declare -a DEFAULT_NAMESPACES=(
    "openstack"
    "openstack-operators"
    "baremetal-operator-system"
    "openshift-machine-api"
    "cert-manager"
    "openshift-nmstate"
)
export DEFAULT_NAMESPACES

METALLB_NAMESPACE=${METALLB_NAMESPACE:-"metallb-system"}

NAMESPACE_PATH=${BASE_COLLECTION_PATH}/namespaces
export NAMESPACE_PATH

# k8s services that must be gather from the openstack
# ctlplane namespace
declare resources=(
    "services"
    "routes"
    "daemonset"
    "replicaset"
    "deployments"
    "statefulset"
    "buildconfig"
    "jobs"
    "cronjobs"
)
export resources

# list of osp services that might be present in the ctlplane
declare -a OSP_SERVICES=(
    "keystone"
    "mariadb"
    "glance"
    "rabbitmq"
    "manila"
    "cinder"
    "nova"
    "horizon"
    "ironic"
    "telemetry"
    "heat"
    "octavia"
    "placement"
    "neutron"
    "swift"
    "ovn"
    "ovs"
    "designate"
    "barbican"
    "dataplane"
)
export OSP_SERVICES


WEBHOOKS_COLLECTION_PATH=${BASE_COLLECTION_PATH}/webhooks
export WEBHOOKS_COLLECTION_PATH

# if a namespace doesn't exist, we don't gather resources
function check_namespace {
    local namespace="$1"
    if /usr/bin/oc get project "$namespace" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# for each resource passed as input, we gather the related
# info in a dedicated directory within the namespace tree
function get_resources {
    local resource="$1"
    local NS="$2"
    mkdir -p "${NAMESPACE_PATH}"/"$NS"/"$resource"
    for res in $(oc -n "$NS" get "$resource" -o custom-columns=":metadata.name"); do
        echo "Dump $resource: $res";
        /usr/bin/oc -n "$NS" get "$resource" "$res" -o yaml > "${NAMESPACE_PATH}"/"$NS"/"$resource"/"$res".yaml
    done
}

# Generic function to expand the DEFAULT_NAMESPACES array where we need to
# check resources.
# e.g. calling <expand_ns "kuttl"> will grow the DEFAULT_NAMESPACES array
# adding all kuttl NS that can be found
function expand_ns {
    local expandkey="$1"
    [ -z "$1" ] && return
    for i in $(oc get project -o=custom-columns=NAME:.metadata.name --no-headers | awk -v k="$expandkey" '$0 ~ k {print $1}'); do
        DEFAULT_NAMESPACES+=("${i}")
    done
}
