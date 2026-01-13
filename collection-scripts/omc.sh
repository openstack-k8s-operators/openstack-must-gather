#!/bin/bash

# OMC compatibility layer
#
# This file provides functions to create omc-compatible structure when
# OMC=true environment variable is set and passed to gather_run
# This collection method is entirely based on `oc adm inspect`

# explicitly include gather_secrets functions to be able to decode (and mask)
# the secrets associated to the openstack services even in OMC mode


# Optionally load dependencies if required
if [[ -z "$DIR_NAME" ]]; then
    CALLED=1
    DIR_NAME=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    source "${DIR_NAME}/common.sh"
fi

if ! declare -f gather_secrets >/dev/null 2>&1; then
    source "${DIR_NAME}/gather_secrets"
fi

# Gather nodes
function collect_nodes_omc {
    [[ "${OMC}" != "true" ]] && return

    for node in $(/usr/bin/oc get nodes -o custom-columns=NAME:.metadata.name --no-headers); do
        run_bg oc adm inspect node "$node" --dest-dir="${BASE_COLLECTION_PATH}"
    done
}

# Gather CRs
function collect_crs_omc {
    for i in $(get_matching_crds)
    do
      crs+=("$i")
    done

    crs+=("baremetalhosts.metal3.io")

    for res in "${crs[@]}"; do
        /usr/bin/oc get "${res}" --all-namespaces -o custom-columns=NAME:.metadata.name,NAMESPACE:.metadata.namespace --no-headers 2> /dev/null | \
        while read -r ocresource; do
            ocobject=$(echo "$ocresource" | awk '{print $1}')
            ocproject=$(echo "$ocresource" | awk '{print $2}')
            if [ -n "${ocproject}" ] && [ "${ocproject}" != "<none>" ]; then
                run_bg oc adm inspect "${res}/${ocobject}" -n "${ocproject}" --dest-dir="${BASE_COLLECTION_PATH}"
            fi
        done
    done
}

# Gather network resources (nncp, nnce, nns, ipaddresspools, l2advertisement)
function collect_network_resources_omc {
    [[ "${OMC}" != "true" ]] && return

    # Collect cluster-scoped network resources
    if oc get nncp &>/dev/null; then
        run_bg oc adm inspect nncp --dest-dir="${BASE_COLLECTION_PATH}"
    fi

    if oc get nnce &>/dev/null; then
        run_bg oc adm inspect nnce --dest-dir="${BASE_COLLECTION_PATH}"
    fi

    if oc get nns &>/dev/null; then
        run_bg oc adm inspect nns --dest-dir="${BASE_COLLECTION_PATH}"
    fi

    # Collect MetalLB resources from metallb-system namespace
    if oc -n "${METALLB_NAMESPACE}" get ipaddresspools &>/dev/null; then
        run_bg oc adm inspect ipaddresspools -n "${METALLB_NAMESPACE}" --dest-dir="${BASE_COLLECTION_PATH}"
    fi

    if oc -n "${METALLB_NAMESPACE}" get l2advertisement &>/dev/null; then
        run_bg oc adm inspect l2advertisement -n "${METALLB_NAMESPACE}" --dest-dir="${BASE_COLLECTION_PATH}"
    fi
}

# Gather all apiservices resources
function collect_apiservices_omc {
    # Get OpenStack and RabbitMQ related APIServices
    for i in $(/usr/bin/oc get apiservices --all-namespaces | awk '/(openstack|rabbitmq)\.(org|com)/ {print $1}'); do
        run_bg oc adm inspect apiservice "$i" --dest-dir="${BASE_COLLECTION_PATH}"
    done
}

# Gather webhooks
function collect_webhooks_omc {
    # Collect validating webhooks
    if oc get validatingwebhookconfiguration &>/dev/null; then
        run_bg oc adm inspect validatingwebhookconfiguration --dest-dir="${BASE_COLLECTION_PATH}"
    fi
    # Collect mutating webhooks
    if oc get mutatingwebhookconfiguration &>/dev/null; then
        run_bg oc adm inspect mutatingwebhookconfiguration --dest-dir="${BASE_COLLECTION_PATH}"
    fi
}

# Post processing actions on gathered files
function collect_omc_post {
    local CMS="core/configmaps.yaml"
    local MASK_OPT=""
    [[ "${DO_NOT_MASK}" -eq 0 ]] && MASK_OPT="--mask"
    for ns in "${DEFAULT_NAMESPACES[@]}"; do
        if check_namespace "$ns"; then
            mkdir -p "$NAMESPACE_PATH/${ns}/configmaps"
            # Split ConfigMapList and apply masking if required
            /usr/bin/cmaps.py "${NAMESPACE_PATH}/${ns}/$CMS" "${NAMESPACE_PATH}/${ns}/configmaps" "$MASK_OPT"
        fi
    done
}

# Main OMC resource gathering
function collect_omc_inspect {
    # Collect cluster-scoped packagemanifests
    if oc get packagemanifest &>/dev/null; then
        run_bg oc adm inspect packagemanifest --dest-dir="${BASE_COLLECTION_PATH}"
    fi

    # Collect CRDs (OpenStack, network, and related domains)
    local all_crds=()
    mapfile -t all_crds < <(get_matching_crds)
    if [[ ${#all_crds[@]} -gt 0 ]]; then
        oc adm inspect crd "${all_crds[@]}" --dest-dir="${BASE_COLLECTION_PATH}" &
    fi
    # Collect namespaced resources
    for ns in "${DEFAULT_NAMESPACES[@]}"; do
        if check_namespace "$ns"; then
            run_bg oc adm inspect -n "$ns" ns/"$ns" --dest-dir="${BASE_COLLECTION_PATH}" &
            # Collect subscriptions, CSVs, installplans
            if oc -n "$ns" get subscriptions &>/dev/null; then
                run_bg oc adm inspect subscriptions -n "$ns" --dest-dir="${BASE_COLLECTION_PATH}"
            fi
            # csv gathering
            if oc -n "$ns" get csv &>/dev/null; then
                run_bg oc adm inspect csv -n "$ns" --dest-dir="${BASE_COLLECTION_PATH}"
            fi
            # installplan gathering
            if oc -n "$ns" get installplan &>/dev/null; then
                run_bg oc adm inspect installplan -n "$ns" --dest-dir="${BASE_COLLECTION_PATH}"
            fi
            # (Note): secrets are collected for each openstack service and
            # contain masked config files: this is not available in OMC mode
            # and we rely on the regular secrets retrieval and masking approach
            gather_secrets "$ns"
        fi
    done

    # inspect resources
    collect_nodes_omc
    collect_apiservices_omc
    collect_crs_omc
    collect_webhooks_omc
    collect_network_resources_omc

    wait
}
