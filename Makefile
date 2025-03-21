IMAGE_REGISTRY ?= quay.io/openstack-k8s-operators
IMAGE_TAG ?= latest

OS_GIT_COMMIT := $(shell git rev-parse --short "HEAD^{commit}")
OS_GIT_BRANCH := $(shell git rev-parse  --abbrev-ref HEAD)
OS_GIT_COMMIT_COUNT := $(shell git rev-list HEAD --count)
OS_GIT_VERSION := $(OS_GIT_BRANCH)-$(OS_GIT_COMMIT_COUNT)-g$(OS_GIT_COMMIT)

BUILD_ARGS ?= --build-arg OS_GIT_VERSION=${OS_GIT_VERSION}

check-image: ## Check if the MUST_GATHER_IMAGE variable is set
ifndef MUST_GATHER_IMAGE
	$(error MUST_GATHER_IMAGE is not set.)
endif

build: check-image podman-build podman-push ## Build and push the must-gather image

check: ## Run sanity check against the script collection
	shellcheck collection-scripts/*

pytest: ## Run sanity check against python scripts in pydir
	tox -c pyscripts/tox.ini

podman-build: check-image ## build the must-gather image
	podman build -t ${IMAGE_REGISTRY}/${MUST_GATHER_IMAGE}:${IMAGE_TAG} ${BUILD_ARGS} .

podman-push: check-image ## push the must-gather image to the image registry
	podman push ${IMAGE_REGISTRY}/${MUST_GATHER_IMAGE}:${IMAGE_TAG}

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: build podman-build podman-push
