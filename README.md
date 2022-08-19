# SLATE CI Docker Images

This repository holds the Dockerfiles for SLATE CI-specific container images.

* Container images will be rebuilt when there is a change to a folder tracked by `build_folders.txt`.
* Images in the `master` branch will automatically receive the 'latest' tag.

## Features

1. Automatically builds and pushes Docker images on changes.
2. Build failure in one folder will not prevent other builds in other folders.
3. Encourages `Dockerfile` best practices with lint, scan etc.
4. Automatically adds [OCI](https://github.com/opencontainers/image-spec/blob/main/annotations.md) labels to every built Docker image as defined in each `Dockerfile`.

## Adding a New Image

Copy `./examples` to a new folder and:
1. Add the new folder name to `build_folders.txt`
2. Update the `LABEL`s in `./<new folder>/Dockerfile` using the [OpenContainers spec](https://github.com/opencontainers/image-spec/blob/main/annotations.md).

## Updating an Existing Image

Make your changes to an image (e.g. `./<your folder>/`) and increment the `org.opencontainers.image.version` label in `./<your folder>/Dockerfile`. Pushing your changes to `master` will automatically trigger a new image build.

## Pull Requests

When a pull request is made to this repo Dockle lint and Trivy scans will run.

## FAQ

### Where are containers pushed to?

Containers are currently pushed to OSG Harbor (specifically to the [hub.opensciencegrid.org/slate](https://hub.opensciencegrid.org/harbor/projects/50/repositories) project).

### How should I update container dependencies?

Increment the minor number of the `org.opencontainers.image.version` label in the associated `Dockerfile`.

## Development

GitHub workflow files are stored in `.github/workflows`.