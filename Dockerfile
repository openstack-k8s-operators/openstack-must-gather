FROM quay.io/openshift/origin-must-gather:4.13.0 as builder

FROM quay.io/centos/centos:stream9

RUN dnf update -y && dnf install rsync python3-pyyaml -y && dnf clean all

COPY --from=builder /usr/bin/oc /usr/bin/oc

# Save original gather script
COPY --from=builder /usr/bin/gather /usr/bin/gather_original

# Copy all collection scripts to /usr/bin
COPY collection-scripts/* /usr/bin/

# Copy the python script used to mask sensitive data
COPY pyscripts/mask.py /usr/bin/

# Entrypoint not used when calling `oc adm must-gather`
ENTRYPOINT /usr/bin/gather
