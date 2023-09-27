# openstack-must-gather

`must-gather` is a tool built on top of [OpenShift must-gather](https://github.com/openshift/must-gather)
that provides the scripts for an OpenStack control plane logs and data collection.

## Usage

```sh
oc adm must-gather --image=quay.io/openstack-k8s-operators/must-gather
```

The command above will create a local directory where logs, configs and status
of the OpenStack control plane services are dumped.

In particular the `openstack-must-gather` will get a dump of:
- Service logs: Retrieved by the output of the pods (and operators) associated to the deployed
  services
- Services config: Retrieved for each component by the deployed `ConfigMaps` and `Secrets`
- Status of the services deployed in the OpenStack control plane
- Deployed CRs and CRDs
- `CSVs`, `pkgmanifests`, `subscriptions`, `installplans`, `operatorgroup`
- `Pods`, `Deployments`, `Statefulsets`, `ReplicaSets`, `Service`, `Routes`, `ConfigMaps`, (part of / relevant) `Secrets`
- Network related info (`Metallb` info, `IPAddressPool`, `L2Advertisements`, `NetConfig`, `IPSet`)

## Development

You can build the image locally using the Dockerfile included.
A `Makefile` is also provided. To use it, you must pass:
- an image name using the variable `MUST_GATHER_IMAGE`.
- an image registry using the variable `IMAGE_REGISTRY` (default is [quay.io/openstack-k8s-operators](https://quay.io/openstack-k8s-operators))
- an image tag using the variable `IMAGE_TAG` (default is `latest`)

The targets for `make` are as follows:
- `check-image`: Check if the `MUST_GATHER_IMAGE` variable is set
- `build`: build the image with the supplied name and pushes it
- `check`: Run sanity check against the script collection
- `pytest`: Run sanity check and unit tests against the python script collection
- `podman-build`: builds the must-gather image
- `podman-push`:  pushes an already-built `must-gather` image

## Example

(optional) Build and push the must-gather image to a registry:

```
git clone ssh://git@github.com/openstack-k8s-operators/openstack-must-gather.git
cd openstack-must-gather
IMAGE_TAG=<tag> IMAGE_REGISTRY=<registry> MUST_GATHER_IMAGE=must-gather make
```

On a machine where you have `oc adm` access, do the following:

```
oc adm must-gather --image=<registry>/must-gather:<tag>
```

When generation is finished, you will find the dump in the current directory
under `must-gather.local.XXXXXXXXXX`.

### Note

If the image is pushed to `quay.io` registry, make sure it's set to `public`,
otherwise it can't be consumed by the must-gather tool.
