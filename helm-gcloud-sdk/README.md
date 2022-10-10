# helm-gcloud-sdk

This is the container for Helm and the Google Cloud SDK.

## Quick Try

### Prepare Environment

1. Create a new `.env` from the `./helm-gcloud-sdk/.env.tmpl` in this repository and place it at the base of the desired mount point for the image (e.g. `/path/to/helm-slate-api/.env`).
2. Replace the placeholder content with actual values.

### Example Commands

```shell
[your@localmachine helm-slate-api]$ docker run -it -v ${PWD}:/work:Z hub.opensciencegrid.org/slate/helm-gcloud-sdk:1.0.0
===================================================
GCloud/Helm Utility Container
===================================================
Activated service account credentials for: <service-account>

To take a quick anonymous survey, run:
  $ gcloud survey

Updated property [core/project].
WARNING: Property validation for compute/zone was skipped.
Updated property [compute/zone].
Fetching cluster endpoint and auth data.
kubeconfig entry generated for <gke-cluster>.
```

```shell
[root@454344d8c4ca work]# kubectl get pods
NAME                                    READY   STATUS             RESTARTS          AGE
development-slate-api-bb7865d57-64mns   1/1     <status>           2176 (6s ago)     7d17h
development-test-27517090--1-67zkj      0/1     <status>           0                 8d
```

## Image Includes

* Google Cloud SDK 405.0.0

## Examples

See [Helm Commands](https://docs.google.com/document/d/1Tn31mUMoJpKJrSvxemOAgS39NkJLQPk_AN5YwUfk4gM/edit#).