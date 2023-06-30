FROM quay.io/openshift/origin-must-gather:4.13.0 as builder

FROM quay.io/centos/centos:stream8

RUN dnf update -y && dnf install rsync -y && dnf clean all

COPY --from=builder /usr/bin/oc /usr/bin/oc

# Save original gather script
COPY --from=builder /usr/bin/gather /usr/bin/gather_original

# Copy all collection scripts to /usr/bin
COPY collection-scripts/* /usr/bin/

ENTRYPOINT /usr/bin/gather
