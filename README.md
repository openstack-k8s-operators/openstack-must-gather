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
IMAGE_TAG=<tag> IMAGE_REGISTRY=<registry> MUST_GATHER_IMAGE=must-gather make build
```

On a machine where you have `oc adm` access, do the following:

```
oc adm must-gather --image=<registry>/must-gather:<tag>
```

When generation is finished, you will find the dump in the current directory
under `must-gather.local.XXXXXXXXXX`.

It is possible to gather debugging information about specific features by adding
to the `oc adm must-gather` command the `--image-stream` argument.
The must-gather tool supports multiple images, so you can gather data about more
than one feature by running a single command.
Adding `--image-stream` assumes that an image has been imported in an OpenShift
namespace and the associated `imagestream` is available.
To import an image as an `imagestream`, run the following commands:

```
oc project <namespace>
oc import-image <registry>/<image>:<tag> --confirm
```

and double check the `imagestream` exists in the specified namespace.
At this point, run the `oc adm must-gather` command passing one or more
imagestream parameters.
For instance, assuming we import the [kubevirt must-gather image](quay.io/kubevirt/must-gather:latest):
within the existing `openstack` namespace:

```
oc project openstack
oc import-image kubevirt-must-gather --from=quay.io/kubevirt/must-gather:latest --confirm
```
we can combine, in a single command, three different containers executions that
gather different aspects of the same environement.

```
oc adm must-gather --image-stream=openstack/kubevirt-must-gather \
   --image-stream=openshift/must-gather \
   --image=quay.io/openstack-k8s-operators/must-gather:latest
```

The command above will create three pods associated to the existing `imagestream`
objects that point to `openstack`, `openshift` and `kubevirt` must-gather container
images.

```
[must-gather] OUT pod for plug-in image quay.io/openstack-k8s-operators/must-gather:latest created
[must-gather] OUT pod for plug-in image quay.io/kubevirt/must-gather@sha256:501e30ac7d5b9840a918bb9e5aa830686288ccfeee37d70aaf99cd2e302a2bb0 created
[must-gather] OUT pod for plug-in image quay.io/openshift-release-dev/ocp-v4.0-art-dev@sha256:e9601b492cbb375f0a05310efa6025691f8bba6a97667976cd4baf4adf0f244c created
...
...
```

### Note

If the image is pushed to `quay.io` registry, make sure it's set to `public`,
otherwise it can't be consumed by the must-gather tool.
