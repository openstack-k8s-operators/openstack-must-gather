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
- `SOS_EDPM_PROFILES`: List of sos report profiles to use. Empty string to run
  them all. Defaults to: `container,openstack_edpm,system,storage,virt`
- `SOS_EDPM_PLUGINS`: List of sos report plugins to use. This is optional.
- `OPENSTACK_DATABASES`: comma separated list of OpenStack databases that should
  be dumped. It is possible to set it to `ALL` and dump all databases. By default
  this env var is unset, hence the database dump is skipped.
- `ADDITIONAL_NAMESPACES`: comma separated list of additional namespaces where
  we want to gather the associated resources.
- `DO_NOT_MASK`: This is an option for **CI only** purposes. It's set to 0 by
  default (and preserves the default behavior required in a production environment).
  However, if set to 1, it dumps secrets and services config files without masking
  sensitive data.

### Inspect gathered data

openstack-must-gather is capable of getting both the kubernetes resources
defined in the collection-scripts, and the sos-reports associated with both the
CoreOS nodes and the EDPM ones.
When the `openstack-must-gather` execution ends, a directory containing all the
gathered resources is generated, and in general it contains:

1. **Global resources**: useful to get some context about the status of the
   openshift cluster and the openstack deployed resources. These resources
   include `crds`, `apiservices`, `csvs`, `packagemanifests`, `webhooks` and
   `network` related informations like `nncp`, `nnce`, `IPAddressPool`, and so
   forth

2. **Namespaced resources**: critical to get the status of the `OpenStack`
   cluster and troubleshoot any problematic situation

3. **sos-reports**: gathered from both the `CoreOS` nodes that are part of the
   `OpenShift` cluster, and the `EDPM` nodes in case are part of the cluster; the
   information to connect to the EDPM nodes is retrieved by the
   `OpenStackDataplaneNodeSets` CR, and the resulting sos-report is retrieved
   from the remote nodes and downloaded in the current must-gather directory

4. **OpenStack Ctlplane Services**: commands run through the `openstack-cli` to
   check the relevant resources generated within the OpenStack cluster (`endpoint
   list`, `networks`, `subnets`, `registered services`, etc)

A generic output of the `openstack-must-gather` execution looks like the
following:


```bash
+-----------------------------------+
|     .                             |                                    +-----------------------------+
|     ├── apiservices               |                                    |    ctlplane/neutron/        |
|     ├── crd                       |                                    |    ├── agent_list           |
|     ├── csv                       |       (control plane resources)    |    ├── extension_list       |
|     ├── ctlplane                  |------------------------------------|    ├── floating_ip_list     |
|     │   ├── neutron               |                                    |    ├── network_list         |
|     │   ├── nova                  |-----------------                   |    ├── port_list            |
|     │   └── placement             |                |                   |    ├── router_list          |
|     ├── dbs                       |   +---------------------------+    |    ├── security_group_list  |
|     ├── namespaces                |   |   namespaces/openstack/   |    |    └── subnet_list          |
|     │   ├── cert-manager          |   |    ├── all_resources.log  |    +-----------------------------+
|     │   ├── openshift-machine-api |   |    ├── buildconfig        |-----------------------------------
|     │   ├── openshift-nmstate     |   |    ├── configmaps         |                                  |
|     │   ├── openstack             |   |    ├── cronjobs           |   +--------------------------------------------------------------------+
|     │   └── openstack-operators   |   |    ├── crs                |   |    namespaces/openstack/secrets/glance/                            |
|     ├── network                   |   |    ├── daemonset          |   |    ├── cert-glance-default-public-route.yaml                       |
|     │   ├── ipaddresspools        |   |    ├── deployments        |   |    ├── glance-config-data.yaml                                     |
|     │   ├── nnce                  |   |    ├── events.log         |   |    ├── glance-config-data.yaml-00-config.conf                      |
|     │   └── nncp                  |   |    ├── installplans       |   |    ├── glance-default-single-config-data.yaml                      |
|     ├── nodes                     |   |    ├── jobs               |   |    ├── glance-default-single-config-data.yaml-00-config.conf       |
|     ├── sos-reports               |   |    ├── nad.log            |   |    ├── glance-default-single-config-data.yaml-10-glance-httpd.conf |
|     │   ├── _all_nodes            |   |    ├── pods               |   |    ├── glance-default-single-config-data.yaml-httpd.conf           |
|     │   ├── barbican              |   |    ├── pvc.log            |   |    ├── glance-default-single-config-data.yaml-ssl.conf             |
|     │   ├── ceilometer            |   |    ├── replicaset         |   |    └── glance-scripts.yaml                                         |
|     │   ├── glance                |   |    ├── routes             |   +--------------------------------------------------------------------+
|     │   ├── keystone              |   |    ├── secrets            |                                  |
|     │   ├── neutron               |   |    ├── services           |   +--------------------------------------------------------------------+
|     │   ├── nova                  |   |    ├── statefulsets       |   | Note: if DO_NOT_MASK is passed in CI, secrets are dumped without   |
|     │   ├── ovn                   |   |    └── subscriptions      |   |       hiding any sensitive information.                            |
|     │   ├── ovs                   |   +---------------------------+   +--------------------------------------------------------------------+
|     │   ├── placement             |
|     │   └── swift                 |
|     └── webhooks                  |
|         ├── mutating              |
|         └── validating            |
+-----------------------------------+
```

In a troubleshooting session, however, it's critical to check and analyze not
only `Secrets` and services config files, but also the `CRs` associated with
each service and the `Pod` logs.
These are still namespaced resources, and they can be found in the CRs and Pods
directories.
Other than that, for each namespace some generic informations is collected. In
particular the `openstack-must-gather` tool is able to retrieve:

1. `Events` recorded for the current namespace
2. `Network Attachment Definitions`
3. `PVCs` attached to the deployed Pods
4. A picture of the namespaces in terms of deployed resources (`all_resources.log`)

```bash
+---------------------------+
| namespaces/openstack/     | ------------------------------------
|    ├── buildconfig        |                                    |
|    ├── cronjobs           |          +--------------------------------------------------------+
|    ├── crs                |          |   namespaces/openstack/crs/                            |
|    ├── daemonset          |          |   ├── barbicanapis.barbican.openstack.org              |
|    ├── deployments        |          |   ├── barbicankeystonelisteners.barbican.openstack.org |
|    ├── events.log         |          |   ├── barbicans.barbican.openstack.org                 |
|    ├── installplans       |          |   ├── barbicanworkers.barbican.openstack.org           |
|    ├── jobs               |          |   ...                                                  |
|    ├── nad.log            |          |   ...                                                  |
|    ├── pods               |          |   ├── glanceapis.glance.openstack.org                  |
|    ├── all_resources.log  |          |          └── glance-default-single.yaml                |
|    ├── configmaps         |          |   ├── glances.glance.openstack.org                     |
|    ├── pvc.log            |          |          └── glance.yaml                               |
|    ├── replicaset         |          |   ├── keystoneapis.keystone.openstack.org              |
|    ├── routes             |          |   ├── keystoneendpoints.keystone.openstack.org         |
|    ├── secrets            |          |   ├── keystoneservices.keystone.openstack.org          |
|    ├── services           |          |   ...                                                  |
|    ├── statefulsets       |          |   ├── telemetries.telemetry.openstack.org              |
|    └── subscriptions      |          |   └── transporturls.rabbitmq.openstack.org             |
+---------------------------+          +--------------------------------------------------------+
```

As depicted in the schema above, the same pattern applies to the Pod resources.
For each `Pod` the openstack-must-gather tool is able to retrieve the
description and the associated logs (including `-previous` in case the Pod is
in a `CrashLookBackoff` status).

```bash
+---------------------------+
| namespaces/openstack/     | ------------------------------------
|    ├── buildconfig        |                                    |
|    ├── cronjobs           |          +-----------------------------------------------------------+
|    ├── crs                |          |   namespaces/openstack/pods/glance-dbpurge-28500481-f4jk9 |
|    ├── daemonset          |          |   ├── glance-dbpurge-28500481-f4jk9-describe              |
|    ├── deployments        |          |   └── logs                                                |
|    ├── events.log         |          |       └── glance-dbpurge.log                              |
|    ├── installplans       |          |   namespaces/openstack/pods/glance-default-single-0       |
|    ├── jobs               |          |   ├── glance-default-single-0-describe                    |
|    ├── nad.log            |          |   └── logs                                                |
|    ├── pods               |          |       ├── glance-api.log                                  |
|    ├── all_resources.log  |          |       ├── glance-httpd.log                                |
|    ├── configmaps         |          |       └── glance-log.log                                  |
|    ├── pvc.log            |          |   namespaces/openstack/pods/glance-default-single-1       |
|    ├── replicaset         |          |   ├── glance-default-single-1-describe                    |
|    ├── routes             |          |   └── logs                                                |
|    ├── secrets            |          |       ├── glance-api.log                                  |
|    ├── services           |          |       ├── glance-httpd.log                                |
|    ├── statefulsets       |          |       └── glance-log.log                                  |
|    └── subscriptions      |          |   namespaces/openstack/pods/glance-default-single-2       |
+---------------------------+          |   ├── glance-default-single-2-describe                    |
                                       |   └── logs                                                |
                                       |       ├── glance-api.log                                  |
                                       |       ├── glance-httpd.log                                |
                                       |       └── glance-log.log                                  |
                                       +-----------------------------------------------------------+
```

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
oc -n openshift-must-gather-b9fpw rsh must-gather-mxc7k
```

And then if we were debugging a bash script called `gather_trigger_gmr`, we
would run it in debug mode:

```bash
sh-5.1# bash -x /usr/bin/gather_trigger_gmr
```

And once we had the script working as intended we would copy the file from a
terminal:

```bash
oc cp openshift-must-gather-b9fpw/must-gather-mxc7k:usr/bin/gather_trigger_gmr collection-scripts/gather_trigger_gmr
```

And finally, from  inside the container shell we let the `oc adm must-gather`
command complete, optionally running everything to ensure we haven't
inadvertently broken anything in the process:

```sh
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

```bash
git clone ssh://git@github.com/openstack-k8s-operators/openstack-must-gather.git
cd openstack-must-gather
IMAGE_TAG=<tag> IMAGE_REGISTRY=<registry> MUST_GATHER_IMAGE=openstack-must-gather make build
```

On a machine where you have `oc adm` access, do the following:

```bash
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

```bash
oc project <namespace>
oc import-image <registry>/<image>:<tag> --confirm
```

and double check the `imagestream` exists in the specified namespace.
At this point, run the `oc adm must-gather` command passing one or more
imagestream parameters.
For instance, assuming we import the [kubevirt must-gather image](quay.io/kubevirt/must-gather:latest):
within the existing `openstack` namespace:

```bash
oc project openstack
oc import-image kubevirt-must-gather --from=quay.io/kubevirt/must-gather:latest --confirm
```

we can combine, in a single command, three different containers executions that
gather different aspects of the same environement.

```bash
oc adm must-gather --image-stream=openstack/kubevirt-must-gather \
   --image-stream=openshift/must-gather \
   --image=quay.io/openstack-k8s-operators/openstack-must-gather:latest
```

The command above will create three pods associated to the existing `imagestream`
objects that point to `openstack`, `openshift` and `kubevirt` must-gather container
images.

```bash
[must-gather] OUT pod for plug-in image quay.io/openstack-k8s-operators/openstack-must-gather:latest created
[must-gather] OUT pod for plug-in image quay.io/kubevirt/must-gather@sha256:501e30ac7d5b9840a918bb9e5aa830686288ccfeee37d70aaf99cd2e302a2bb0 created
[must-gather] OUT pod for plug-in image quay.io/openshift-release-dev/ocp-v4.0-art-dev@sha256:e9601b492cbb375f0a05310efa6025691f8bba6a97667976cd4baf4adf0f244c created
...
...
```

### `sos report` from nodes

To gather config files and logs from hosts we need to rely on the `sos` tool (former `sosreport`).

We can obtain logs from both OCP cluster nodes and compute nodes.

#### OCP Cluster nodes

First we need to gather cluster host names

```bash
$ oc get nodes -o name
node/master-0
node/master-1
node/master-2
```

Then we need to login into a node via a debug container

```bash
$ oc debug node/master-0
Warning: would violate PodSecurity "restricted:v1.24": host namespaces (hostNetwork=true, hostPID=true, hostIPC=true), privileged (container "container-00" must not set securityContext.privileged=true), allowPrivilegeEscalation != false (container "container-00" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "container-00" must set securityContext.capabilities.drop=["ALL"]), restricted volume types (volume "host" uses restricted volume type "hostPath"), runAsNonRoot != true (pod or container "container-00" must set securityContext.runAsNonRoot=true), runAsUser=0 (container "container-00" must not set runAsUser=0), seccompProfile (pod or container "container-00" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
Starting pod/master-0-debug-lpvnn ...
To use host binaries, run `chroot /host`
Pod IP: 192.168.111.20
If you don't see a command prompt, try pressing enter.
sh-4.4#
```

We need to chroot into the node itself in order to have access to all commands

```bash
sh-4.4# chroot /host
sh-5.1#
```

We need to spawn a [toolbox](https://containertoolbx.org/install/) container to use `sos` tool.

```bash
sh-5.1# toolbox
Trying to pull registry.redhat.io/rhel9/support-tools:latest...
Getting image source signatures
Checking if image destination supports signatures
Copying blob bf237f774da8 done
Copying blob 4b36affe1d29 done
Copying config d184fda91f done
Writing manifest to image destination
Storing signatures
d184fda91f0aa5c6deed433f984bd393754f707a285445a83637aaa13b8b7e86
Spawning a container 'toolbox-root' with image 'registry.redhat.io/rhel9/support-tools'
Detected RUN label in the container image. Using that as the default...
57305547f44861347e453b535fd59a56b4d9c0a3f472b7f1d86c2f246c94a5ea
toolbox-root
Container started successfully. To exit, type 'exit'.
[root@master-0 /]#
```

Finally we can collect all required config/logs

```bash
[root@master-0 /]# sos report -k crio.all=on -k crio.logs=on
<snip output>
  Finished running plugins
Creating compressed archive...

Your sosreport has been generated and saved in:
  /host/var/tmp/sosreport-master-0-2023-11-15-mvgdmxo.tar.xz

 Size 82.68MiB
 Owner  root
 sha256 81b356f0069b4bc35dc4ae016e2c25369c9cefa214c75973cde8b8470ffa4516

Please send this file to your support representative.

[root@master-0 /]#
```

You can also add the flag `--all-logs` to the `sos` command to retrieve further configuration file and logs

For more information see the official OCP documentation [here](https://docs.openshift.com/container-platform/4.13/support/gathering-cluster-data.html)

#### EDPM compute nodes

First we need to gather compute node info from `OpenstackDataPlaneNodeSet` resources.

```bash
$ oc get openstackdataplanenodesets -o name
openstackdataplanenodeset.dataplane.openstack.org/openstack-edpm-ipam
$ oc get openstackdataplanenodeset.dataplane.openstack.org/openstack-edpm-ipam -o json | jq -r '.spec.nodes[] | [.hostName, .ansible.ansibleHost] | @csv'
"edpm-compute-0","192.168.122.100"
"edpm-compute-1","192.168.122.101"
"edpm-compute-2","192.168.122.102"
```

Then you have to login into nodes via ssh. In the `OpenstackDataplaneNodeSet` resource you can find the user used by ansible and the private ssh, that we can extract from the secret.

```bash
# user
$ oc get openstackdataplanenodeset.dataplane.openstack.org/openstack-edpm-ipam -o json | jq .spec.nodeTemplate.ansible.ansibleUser
"zuul"
# private ssh key
$ oc get openstackdataplanenodeset.dataplane.openstack.org/openstack-edpm-ipam -o json |jq .spec.nodeTemplate.ansibleSSHPrivateKeySecret
"dataplane-ansible-ssh-private-key-secret"
# save private ssh key to a file and fix its permissions
$ oc get secret/dataplane-ansible-ssh-private-key-secret -o go-template='{{ index .data "ssh-privatekey" | base64decode }}'  > ~/.ssh/compute.key
$ chmod 0600 ~/.ssh/compute.key
```

Finally login into compute node

```bash
$ ssh -i ~/.ssh/compute.key zuul@192.168.122.100
Register this system with Red Hat Insights: insights-client --register
Create an account or view all your systems at https://red.ht/insights-dashboard
Last login: Wed Nov 15 10:02:11 2023 from 192.168.111.1
[zuul@compute-0 ~]$
```

And launch the `sos` command just like we did in the other example, but with different flags.

```bash
sudo sos report -p system,storage,virt,openstack_edpm
```

As you can see in the example above, there's a new profile for the `sos` tool, `openstack_edpm`, which enables the gathering from the plugins running on the node.

The output file `/var/tmp/sosreport-$hostname-$date-$hash.tar.xz` will contains all the required files from paths introduced in the new containerized services, like `/var/lib/openstack/`, `/var/lib/edpm-config`, `/var/log/containers/` and so on.

### Note

If the image is pushed to `quay.io` registry, make sure it's set to `public`,
otherwise it can't be consumed by the must-gather tool.
