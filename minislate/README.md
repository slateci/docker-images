# minislate

This is the container used by Minislate for local SLATE app development.

## Quick Try

See [slateci/minislate](https://github.com/slateci/minislate) for instructions.

## Image Includes

* Rancher
* Kubectl
* Helm 3
* SLATE API Server
* SLATE CLI
* SLATE Portal app
* Docker environmental variables:
  * `KUBECONFIG`
    * Default value is `/etc/rancher/k3s/k3s.yaml` 
* Docker image arguments:
  * `endpoint`
    * Default value is `'http://localhost:18080'`
  * `portalbranch`
    * Default value is `master`
  * `token`
    * Default value is `'5B121807-7D5D-407A-8E22-5F001EF594D4'`

## Examples

See [slateci/minislate](https://github.com/slateci/minislate).