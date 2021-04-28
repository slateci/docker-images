#!/usr/bin/env python3

"""
Builds Docker images found in github.com/slateci/docker-images.

This script assumes the following:
1. pyyaml Python package is installed.
2. hadolint is installed and on $PATH.
3. `docker scan` plugin is installed.
4. Docker Buildx is configured to be used by default.
5. `docker login` has been called for each registry.
"""

import argparse
import datetime
import subprocess
from functools import partial
from os import path
from sys import stdout
from typing import Any, Dict, List, Optional, Set, Tuple, cast

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

BUILD_FOLDERS_FILE = "build_folders.txt"

LABEL_SCHEMA_FIELDS = ["name", "description", "maintainer", "usage", "url", "version"]
SLATE_FIELDS = ["maintainer"]

IMAGE_URLS = ["ghcr.io/slateci", "hub.opensciencegrid.org/slate"]

# Force print to flush each time it's called.
print = partial(print, flush=True)

### Helper Functions ###
# See https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions#grouping-log-lines
# for information about these ::keyword:: messages.
def gh_error(msg: str) -> None:
    print("::error::" + msg)


def gh_warning(msg: str) -> None:
    print("::warning::" + msg)


def get_build_folders() -> Set[str]:
    with open(BUILD_FOLDERS_FILE) as f:
        return set(f.read().splitlines())


def get_changed_folders(from_commit: str, to_commit: str) -> Set[str]:
    # Get the list of folders we should be building.
    folders = get_build_folders()

    # Get the list of folders that have changes from the last commit.
    git_diff = subprocess.run(
        ["git", "diff", "--name-only", f"{from_commit}..{to_commit}"],
        capture_output=True,
    )

    # Return only the folders we care about.
    return (
        set(map(lambda x: x.split("/")[0], git_diff.stdout.decode().splitlines()))
        & folders
    )


def check_required_files(folder: str) -> bool:
    if not path.isfile(f"{folder}/Dockerfile"):
        gh_error("Dockerfile not found!")
        return False

    if not path.isfile(f"{folder}/metadata.yml"):
        gh_error("metadata.yml not found!")
        return False

    return True


def get_metadata(
    folder: str, branch: Optional[str] = None
) -> Optional[Tuple[Dict[str, Any], List[str]]]:
    try:
        with open(f"{folder}/metadata.yml") as f:
            metadata = yaml.load(f.read(), Loader=Loader)
    except Exception as e:
        gh_error(f"Failed to read metadata.yml: {e}")
        return None

    if not isinstance(metadata, dict):
        gh_error("Unexpected metadata.yml format!")
        return None
    else:
        metadata = cast(Dict[str, Any], metadata)

    if "name" not in metadata or metadata["name"] is None or metadata["name"] == "":
        gh_error("'name' field missing in metadata.yml!")
        return None

    if (
        "version" not in metadata
        or metadata["version"] is None
        or metadata["version"] == ""
    ):
        gh_error("'version' field missing in metadata.yml!")
        return None

    if metadata["version"] == "latest":
        gh_error("'version' field is prohibited to be 'latest'.")
        return None

    tags = []
    for url in IMAGE_URLS:
        if branch and not branch == "stable":
            tags.append(f"{url}/{metadata['name']}:{branch}")
        else:
            tags.append(f"{url}/{metadata['name']}:{metadata['version']}")
            tags.append(f"{url}/{metadata['name']}:latest")

    return metadata, tags


### Check if Version Exists ###
def check_version_exists(tags: List[str]) -> bool:
    for t in tags:
        if t.endswith(":latest"):
            continue

        check = subprocess.run(
            ["docker", "manifest", "inspect", t], capture_output=True
        )

        if check.returncode == 0:
            gh_error(f"{t} already exists, stopping...")
            print(
                "Overriding existing versions of a container is _dangerous_ "
                "and should be avoided if possible. We recommend incrementing "
                "the version number in metadata.yml instead or ignoring this "
                "error if these commits do not substantially change the container "
                "(e.g. adding whitespace / comments to files). If you know what "
                "you are doing, you can force a build/push from the Actions tab."
            )
            return True

    return False


### Lint ###
def lint_folder(folder: str) -> bool:
    print(">>>> Lint Dockerfile <<<<")

    lint_output = subprocess.run(
        ["hadolint", "--no-fail", "Dockerfile"], capture_output=True, cwd=folder
    )

    lint_stdout = lint_output.stdout.decode().strip()
    print(lint_stdout)

    if lint_output.returncode != 0:
        gh_error("Failed to lint Dockerfile!")
        return False

    if "error" in lint_stdout:
        gh_error("Dockerfile failed linter test!")
        return False

    print(">> Lint successful! <<")

    return True


### Build ###
def build_folder(folder: str, metadata: Dict[str, Any], tags: List[str]) -> bool:
    print(">>>> Build Image <<<<")

    labels = {}
    for field in LABEL_SCHEMA_FIELDS:
        if field in metadata and metadata[field] is not None and metadata[field] != "":
            labels[f"org.label-schema.{field}"] = metadata[field]

    for field in SLATE_FIELDS:
        if field in metadata and metadata[field] is not None and metadata[field] != "":
            labels[f"io.slateci.{field}"] = metadata[field]

    labels["org.label-schema.vendor"] = "SLATE CI"
    labels["org.label-schema.build-date"] = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()
    labels["org.label-schema.vcs-url"] = "https://github.com/slateci/docker-images"
    labels["org.label-schema.vcs-ref"] = (
        subprocess.run(
            ["git", "log", "-n", "1", "--pretty=format:%H", "--", folder],
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )

    labels_flags = []
    for k, v in labels.items():
        labels_flags += ["--label", f"{k}={v}"]

    tag_flags = []
    for t in tags:
        tag_flags += ["--tag", t]

    # Clean Docker cache
    cache_clean = subprocess.run(["docker", "buildx", "prune", "-a", "-f"])

    if cache_clean.returncode != 0:
        gh_error("Failed to clean build cache!")
        return False

    # Delete all existing Docker images.
    image_clean = subprocess.run(
        ["docker", "rmi", "$(docker images -a -q)", "-f"], shell=True
    )

    if image_clean.returncode != 0:
        gh_error("Failed to clean image cache!")
        return False

    # Pull image caches.
    build_output = subprocess.run(
        [
            "docker",
            "buildx",
            "build",
            ".",
            "--file",
            "Dockerfile",
            f"--cache-from=type=registry,ref={IMAGE_URLS[0]}/{metadata['name']}:latest",
            "--output=type=docker",
            # This appears to be faster and pushes all tags at once but doesn't
            # allow us to scan for vulnerabilities before pushing.
            # "--output=type=registry",
            # Add cache metadata to the image itself.
            # Alternatively, "--cache-to=type=registry" might work.
            "--cache-to=type=inline",
        ]
        + labels_flags
        + tag_flags,
        stdout=stdout,
        cwd=folder,
    )

    if build_output.returncode != 0:
        gh_error("Failed to build!")
        return False

    print(">> Successfully built! <<")
    return True


### Scan for Vulnerabilities ###
def scan_for_vulnerability(folder: str, tags: List[str]) -> bool:
    print(">>>> Scan Image for Vulnerabilities <<<<")

    scan_output = subprocess.run(
        ["docker", "scan", tags[0], "--accept-license"],
        stdout=stdout,
        cwd=folder,
    )

    if scan_output.returncode != 0:
        gh_error("Image failed vulnerability scan!")
        return False

    print(">> Image vulnerability scan came back clean! <<")
    return True


### Push ###
def push_folder(folder: str, tags: List[str]) -> bool:
    print(">>>> Push Image <<<<")

    for t in tags:
        push_output = subprocess.run(["docker", "push", t], stdout=stdout, cwd=folder)

        if push_output.returncode != 0:
            gh_error(f"Failed to push {t}!")
            return False

    print(">> Successfully pushed! <<")
    return True


### Main Functions ###
def pipeline(args: argparse.Namespace) -> int:
    changed_folders = get_changed_folders(args.from_commit, args.to_commit)

    print(f"Detected changes in folders: {', '.join(changed_folders)}")

    failed = []

    for folder in changed_folders:
        print(f"::group::{folder}")

        if not (
            check_required_files(folder)
            and (mt_tuple := get_metadata(folder, args.branch))
            and not (
                False
                if args.ignore_version_check
                else check_version_exists(mt_tuple[1])
            )
            and lint_folder(folder)
            and build_folder(folder, *mt_tuple)
            and scan_for_vulnerability(folder, mt_tuple[1])
            and (True if args.no_push else push_folder(folder, mt_tuple[1]))
        ):
            failed.append(folder)

        print("::endgroup::")

    if len(failed) != 0:
        gh_error(f"The following images failed to build: {', '.join(failed)}")
        return 1

    print("Successfully built all images!")
    return 0


def lint(args: argparse.Namespace, folders: Set[str]) -> int:
    failed = []

    for folder in folders:
        print(f"::group::{folder}")

        if not (
            check_required_files(folder)
            and get_metadata(folder)
            and lint_folder(folder)
        ):
            failed.append(folder)

        print("::endgroup::")

    if len(failed) != 0:
        gh_error(f"The following images failed to lint: {', '.join(failed)}")
        return 1

    print("Successfully linted all images!")
    return 0


def lint_all(args: argparse.Namespace) -> int:
    return lint(args, get_build_folders())


def lint_some(args: argparse.Namespace):
    return lint(args, set(args.folders.split(",")) & get_build_folders())


def force_build(args: argparse.Namespace, folders: Set[str]) -> int:
    failed = []

    for folder in folders:
        print(f"::group::{folder}")

        if not (
            check_required_files(folder)
            and (mt_tuple := get_metadata(folder, args.branch))
            and build_folder(folder, *mt_tuple)
            and push_folder(folder, mt_tuple[1])
        ):
            failed.append(folder)

        print("::endgroup::")

    if len(failed) != 0:
        gh_error(f"The following images failed to build: {', '.join(failed)}")
        return 1

    print("Successfully built all images!")
    return 0


def force_build_all(args: argparse.Namespace):
    return force_build(args, get_build_folders())


def force_build_some(args: argparse.Namespace):
    return force_build(args, set(args.folders.split(",")) & get_build_folders())


parser = argparse.ArgumentParser(
    description="""
Builds Docker images for slateci/docker-images.
Folders must be listed in build_folders.txt for any of these actions.
"""
)
subparsers = parser.add_subparsers()

pipeline_p = subparsers.add_parser(
    "pipeline",
    description="Lint / Build / Push folders that have changed between specified commits.",
    help="Lint / Build / Push folders that have changed between specified commits",
)
pipeline_p.add_argument(
    "from_commit",
    type=str,
    help="commit SHA from which to search for changes (exclusive)",
)
pipeline_p.add_argument(
    "to_commit",
    type=str,
    help="commit SHA to which to search for changes (inclusive)",
)
pipeline_p.add_argument(
    "--no-push", action="store_true", help="build the image but do not push it"
)
pipeline_p.add_argument(
    "--ignore-version-check",
    action="store_true",
    help="push the image even if this version exists",
)
pipeline_p.add_argument(
    "--branch",
    type=str,
    help="branch name to use in tag instead of 'latest' and version",
)
pipeline_p.set_defaults(func=pipeline)

lint_all_p = subparsers.add_parser(
    "lint-all", description="Lint all folders.", help="Lint all folders"
)
lint_all_p.set_defaults(func=lint_all)

lint_some_p = subparsers.add_parser(
    "lint", description="Lint specified folders.", help="Lint some folders"
)
lint_some_p.add_argument(
    "folders",
    help="comma separated list of folders to lint",
)
lint_some_p.set_defaults(func=lint_some)

force_build_all_p = subparsers.add_parser(
    "force-build-all",
    description="Force build and push all folders (ignoring lint, version existence, and vulnerability errors).",
    help="Force build and push all folders (ignoring lint, version existence, and vulnerability errors)",
)
force_build_all_p.add_argument(
    "--branch",
    type=str,
    help="branch name to use in tag instead of 'latest' and version",
)
force_build_all_p.set_defaults(func=force_build_all)

force_build_some_p = subparsers.add_parser(
    "force-build",
    description="Force build and push specified folders (ignoring lint, version existence, and vulnerability errors).",
    help="Force build and push some folders (ignoring lint, version existence, and vulnerability errors)",
)
force_build_some_p.add_argument(
    "folders",
    help="comma separated list of folders to force build",
)
force_build_some_p.add_argument(
    "--branch",
    type=str,
    help="branch name to use in tag instead of 'latest' and version",
)
force_build_some_p.set_defaults(func=force_build_some)

if __name__ == "__main__":
    args = parser.parse_args()
    exit(args.func(args))
