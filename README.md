# openstack-must-gather

`must-gather` is a tool built on top of [OpenShift must-gather](https://github.com/openshift/must-gather)
that provides the scripts for an OpenStack control plane logs and data collection.

## Usage

```sh
oc adm must-gather --image=quay.io/openstack-k8s-operators/openstack-must-gather
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
- SOS reports for OpenShift nodes that are running OpenStack service pods.

### Customize gathered data

Some openstack-must-gather collectors can be configured via environmental
variables to behave differently. For example SOS gathering can be disabled
passing an empty `SOS_SERVICES` environmental variable.

To provide environmental variables we'll need to invoke the gathering command
manually like this:

```sh
oc adm must-gather --image=quay.io/openstack-k8s-operators/openstack-must-gather -- SOS_SERVICES= gather
```

This is the list of available environmental variables:

- `CONCURRENCY`: Must gather runs many operations, so to speed things up we run
  them in parallel with a concurrency of 5 by default. Users can change this
  environmental variable to adjust to its needs.
- `SOS_SERVICES`: Comma separated list of services to gather SOS reports from.
  Empty string skips sos report gathering. Eg: `cinder,glance`. Defaults to all
  of them.
- `SOS_ONLY_PLUGINS`: List of SOS report plugins to use. Empty string to run
  them all. Defaults to: `block,cifs,crio,devicemapper,devices,iscsi,lvm2,
  memory,multipath,nfs,nis,nvme,podman,process,processor,selinux,scsi,udev`.
- `SOS_EDPM`: Comma separated list of edpm nodes to gather SOS reports from,
  empty string skips sos report gathering. Accepts keyword all to gather all
  nodes. eg: `edpm-compute-0,edpm-compute-1`
- `SOS_EDPM_PROFILES`: list of sos report profiles to use. Empty string to run
  them all. Defaults to: `system,storage,virt`

## Development

### Building container

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

### Debugging container

One possible workflow that can be used for development is to run the openstack
must-gather in debug mode:

```bash
$ oc adm must-gather --image=quay.io/openstack-k8s-operators/openstack-must-gather -- gather_debug
[must-gather      ] OUT Using must-gather plug-in image: quay.io/openstack-k8s-operators/openstack-must-gather:latest
When opening a support case, bugzilla, or issue please include the following summary data along with any other requested information:
ClusterID: 6ffe21e8-7dc9-4719-926f-f34ec33e6916
ClusterVersion: Stable at "4.12.35"
ClusterOperators:
	All healthy and stable


[must-gather      ] OUT namespace/openshift-must-gather-b9fpw created
[must-gather      ] OUT clusterrolebinding.rbac.authorization.k8s.io/must-gather-mq6st created
[must-gather      ] OUT pod for plug-in image quay.io/openstack-k8s-operators/openstack-must-gather:latest created
[must-gather-mxc7k] POD 2023-09-29T09:56:24.995284210Z Must gather entering debug mode, will sleep until file /tmp/rm-to-finish-gathering is deleted
[must-gather-mxc7k] POD 2023-09-29T09:56:24.995284210Z
```

Running in debug mode makes the must gather container just sit waiting for a
file to be removed, allowing us to go into the container and test our scripts.
In the above case, where the namespace is `openshift-must-gather-b9fpw` and the
pod name is `must-gather-mxc7k` we would enter the container with:

```bash
$ oc -n openshift-must-gather-b9fpw rsh must-gather-mxc7k
```

And then if we were debugging a bash script called `gather_trigger_gmr`, we
would run it in debug mode:

```bash
sh-5.1# bash -x /usr/bin/gather_trigger_gmr
```

And once we had the script working as intended we would copy the file from a
terminal:

```bash
$ oc cp openshift-must-gather-b9fpw/must-gather-mxc7k:usr/bin/gather_trigger_gmr collection-scripts/gather_trigger_gmr
```

And finally, from  inside the container shell we let the `oc adm must-gather`
command complete, optionally running everything to ensure we haven't
inadvertently broken anything in the process:

```bash
sh-5.1# gather
sh-5.1# rm /tmp/rm-to-finish-gathering
```

### Component specifics

Besides the generic OpenShift etcd objects that must-gather scripts are
currently gathering there's also component specific code that gather other
information, so when adding or improving a component we should look into:

- `collection-scripts/common.sh`: Services are in the `OSP_SERVICES` variable
  to indicate that the script must gather its config maps, secrets, additional
  information, trigger Guru Mediation Reports, etc.

- `collection-scripts/gather_services_status`: Runs OpenStack commands to
  gather additional information. For example for Cinder it gather state of the
  services, volume types, qos specs, volume transfer requests, summary of
  existing volumes, pool information, etc.

- `collection-scripts/gather_trigger_gmr`: Triggers Guru Meditation Reports on
  the services so they are present in the logs when those are gathered
  afterwards.


## Example

(optional) Build and push the must-gather image to a registry:

```
git clone ssh://git@github.com/openstack-k8s-operators/openstack-must-gather.git
cd openstack-must-gather
IMAGE_TAG=<tag> IMAGE_REGISTRY=<registry> MUST_GATHER_IMAGE=openstack-must-gather make build
```

On a machine where you have `oc adm` access, do the following:

```
oc adm must-gather --image=<registry>/openstack-must-gather:<tag>
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
   --image=quay.io/openstack-k8s-operators/openstack-must-gather:latest
```

The command above will create three pods associated to the existing `imagestream`
objects that point to `openstack`, `openshift` and `kubevirt` must-gather container
images.

```
[must-gather] OUT pod for plug-in image quay.io/openstack-k8s-operators/openstack-must-gather:latest created
[must-gather] OUT pod for plug-in image quay.io/kubevirt/must-gather@sha256:501e30ac7d5b9840a918bb9e5aa830686288ccfeee37d70aaf99cd2e302a2bb0 created
[must-gather] OUT pod for plug-in image quay.io/openshift-release-dev/ocp-v4.0-art-dev@sha256:e9601b492cbb375f0a05310efa6025691f8bba6a97667976cd4baf4adf0f244c created
...
...
```

### Note

If the image is pushed to `quay.io` registry, make sure it's set to `public`,
otherwise it can't be consumed by the must-gather tool.
