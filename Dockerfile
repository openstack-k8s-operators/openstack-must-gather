FROM quay.io/openshift/origin-must-gather:4.18.0 as builder

FROM quay.io/centos/centos:stream9

ARG OS_GIT_VERSION

RUN dnf update -y && dnf install jq xz rsync python3-pyyaml openssh-clients -y && dnf clean all

COPY --from=builder /usr/bin/oc /usr/bin/oc

# Save original gather script
COPY --from=builder /usr/bin/gather /usr/bin/gather_original

# Copy all collection scripts to /usr/bin
COPY collection-scripts/* /usr/bin/

# Copy the python script used to mask sensitive data
COPY pyscripts/mask.py /usr/bin/
COPY pyscripts/cmaps.py /usr/bin/

# Set openstack-must-gather image version based on
# the current git info
ENV OS_GIT_VERSION=${OS_GIT_VERSION}

# Entrypoint not used when calling `oc adm must-gather`
ENTRYPOINT /usr/bin/gather
