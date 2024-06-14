FROM quay.io/openshift/origin-must-gather:4.15.0 as builder

FROM quay.io/centos/centos:stream9

ARG openshiftclient

RUN dnf update -y && dnf install jq xz rsync python3-pyyaml openssh-clients -y && dnf clean all

COPY --from=builder /usr/bin/oc /usr/bin/oc

# Save original gather script
COPY --from=builder /usr/bin/gather /usr/bin/gather_original

# Copy all collection scripts to /usr/bin
COPY collection-scripts/* /usr/bin/

# Copy the python script used to mask sensitive data
COPY pyscripts/mask.py /usr/bin/

# When fips is enabled, install the fips complaint openshift-client
RUN if [ "$openshiftclient" != "" ]; then \
    curl -o openshift-client "${openshiftclient}" && \
    tar -xzvf openshift-client && mv ./oc /usr/bin/oc && \
    rm {openshift-client,README.md,kubectl}; \
    fi

# Entrypoint not used when calling `oc adm must-gather`
ENTRYPOINT /usr/bin/gather
