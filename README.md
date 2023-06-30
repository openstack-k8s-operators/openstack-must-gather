# openstack-must-gather

OCP must-gather scripts for osp operator logs/data collection.

## Usage

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
