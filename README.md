# SLATE CI Docker Images
This repository holds the Dockerfiles for SLATE CI specific container images.

Container images will be rebuilt when there is a change to a folder tracked by `build_folders.txt`.
By default, the build script will:
1. Check to ensure the folder has a `Dockerfile` and `metadata.yml` file
2. Check to see if the container version already exists
3. Lint the Dockerfile with `hadolint`
4. Build the container image with Docker buildx
5. Check the container image for vulnerabilities using `docker scan` (temporarily disabled)
6. Push the image to the specified registries

Images in the `stable` branch will automatically receive the 'latest' tag.

## Features
1. Automatically builds and pushes Docker images on changes.
2. Build failure in one folder will not prevent other builds in other folders.
3. Encourages Dockerfile best practices with lint, avoiding version overrides, etc.
4. Automatically adds [label-schema](http://label-schema.org/rc1/) labels to every built Docker image.

## Adding a New Image
Copy the `examples` folder and add the new folder name to `build_folders.txt`.
`metadata.yml` is used by the build script to generate labels for the image.

## Updating an Existing Image
Make your changes to an image and increment the `version` field in `metadata.yml`.
Pushing your changes to `stable` will automatically trigger a new image build.

## Pull Requests
When a pull request is made to this repo, a user with at least write permissions to this repo can enable pull request builds by either applying the 'ok-to-test' label or typing '/ok-to-test' in a comment. Then, any folders that change in the pull request will be built and pushed with the version tag set to 'PR-{PR NUM}-{BRANCH NAME}'.

The version listed in `metadata.yml` will be ignored, but PRs will still check for version conflicts.

## FAQ
### Where are containers pushed to?
Containers are currently pushed to both 'ghcr.io/slateci' and 'hub.opensciencegrid.org/slate'.
Check the '--push-tags' flag in `.github/workflows/*` to verify.

### How do I trigger a lint job?
Go to the 'Actions' tab on the top, click on 'Lint Dockerfiles' on the side, and then 'Run workflow ???'.
Type in 'ALL' to lint all Dockerfiles or a comma separated list of folders (e.g. 'basic-auth,condor-worker') to lint specific folders.
If the job succeeds, the lint went through correctly.

### How do I force build/push an image?
WARNING: This can potentially override existing container versions, which can result in broken charts. This should only be done if you know what you are doing.

Go to the 'Actions' tab on the top, click on 'Force Build and Push Container Images' on the side, and then 'Run workflow ???'.
Type in 'ALL' to force build and push all Dockerfiles, or type in a comma separated list of folders (e.g. 'basic-auth,condor-worker') to force build and push specific folders.
If the job succeeds, all images were successfully built and pushed.

### How should I update container dependencies?
Increment the minor number of the `version` field in `metadata.yml`.

## Development
Github Action files are stored in `.github/workflows`. The build script is located at `build.py`.

## How can I skip specific vulnerabilities scan?
We recommend fixing the vulnerabilities; however, you have a provision to skip scanning your docker image for specific vulnerabilities for any valid reason. You can add the vulnerability tag/tags that you want Trivy and Dockle to ignore in the .trivyignore and .dockleignore files, respectively. Refer example folder for more info.

## Todo
1. Add Github Action cron job for checking image vulnerabilities.
