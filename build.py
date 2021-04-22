#!/usr/bin/env python3

import datetime
import subprocess
from functools import partial
from os import chdir, path
from sys import stdout
from typing import Any, Dict, Optional, Set

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

BUILD_FOLDERS_FILE = "build_folders.txt"

LABEL_SCHEMA_FIELDS = ["name", "description", "maintainer", "usage", "url", "version"]
SLATE_FIELDS = ["maintainer"]

IMAGE_URL = "ghcr.io/slateci"

# TODO:
#   1. Check if the version being built already exists in the registry.
#   2. Add force build/push and lint/scan buttons.
#   3. Push images on non-stable branches (e.g. beta), and clean up those branches after they are merged.
#   4. Change detection should use commit _from last push_.

# Force print to flush each time it's called.
print = partial(print, flush=True)

### Helper Functions ###
def gh_error(msg: str) -> None:
    print("::error::" + msg)


def gh_warning(msg: str) -> None:
    print("::error::" + warning)


def get_changed_folders() -> Set[str]:
    # Get the list of folders we should be building.
    with open(BUILD_FOLDERS_FILE) as f:
        folders = set(f.read().splitlines())

    # Get the list of folders that have changes from the last commit.
    git_diff = subprocess.run(
        ["git", "diff", "--name-only", "HEAD^..HEAD"], capture_output=True
    )

    # Return only the folders we care about.
    return (
        set(map(lambda x: x.split("/")[0], git_diff.stdout.decode().split())) & folders
    )


def check_required_files(folder: str) -> bool:
    if not path.isfile(f"{folder}/Dockerfile"):
        gh_error(f"Dockerfile not found!")
        return False

    if not path.isfile(f"{folder}/metadata.yml"):
        gh_error(f"metadata.yml not found!")
        return False

    return True


def get_metadata(folder: str) -> Optional[Dict[str, Any]]:
    try:
        with open(f"{folder}/metadata.yml") as f:
            metadata = yaml.load(f.read(), Loader=Loader)
    except Exception as e:
        gh_error(f"Failed to read metadata.yml: {e}")
        return None

    if "name" not in metadata or metadata["name"] is None or metadata["name"] == "":
        gh_error(f"'name' field missing in metadata.yml!")
        return None

    if (
        "version" not in metadata
        or metadata["version"] is None
        or metadata["version"] == ""
    ):
        gh_error(f"'version' field missing in metadata.yml!")
        return None

    return metadata


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

    if "error:" in lint_stdout:
        gh_error("Dockerfile failed linter test!")
        return False

    print(">> Lint successful! <<")

    return True


### Build ###
def build_folder(folder: str) -> bool:
    print(">>>> Build Image <<<<")

    metadata = get_metadata(folder)
    if metadata is None:
        return False

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
        subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True)
        .stdout.decode()
        .strip()
    )

    labels_flags = []
    for k, v in labels.items():
        labels_flags += ["--label", f"{k}={v}"]

    image_name_tag = f"{IMAGE_URL}/{metadata['name']}:{metadata['version']}"
    build_output = subprocess.run(
        [
            "docker",
            "build",
            ".",
            "--file",
            "Dockerfile",
            "--tag",
            image_name_tag,
            "--cache-from",
            image_name_tag,
        ]
        + labels_flags,
        stdout=stdout,
        cwd=folder,
    )

    if build_output.returncode != 0:
        gh_error("Failed to build!")
        return False

    print(f">> Successfully built! <<")
    return True


### Push ###
# Assumes docker login has already been done.
def push_folder(folder: str) -> bool:
    print(">>>> Push Image <<<<")

    metadata = get_metadata(folder)
    if metadata is None:
        return False

    image_name_tag = f"{IMAGE_URL}/{metadata['name']}:{metadata['version']}"

    push_output = subprocess.run(
        ["docker", "push", image_name_tag], stdout=stdout, cwd=folder
    )

    if push_output.returncode != 0:
        gh_error("Failed to push!")
        return False

    print(f">> Successfully pushed! <<")
    return True


### Scan for Vulnerabilities ###
def scan_for_vulnerability(folder: str) -> bool:
    pass


### Main Functions ###
def folder_pipeline(folder: str) -> bool:
    print(f"::group::{folder}")

    if not check_required_files(folder):
        print("::endgroup::")
        return False

    # Lint
    if not lint_folder(folder):
        print("::endgroup::")
        return False

    # Build
    if not build_folder(folder):
        print("::endgroup::")
        return False

    # Scan for Vulnerabilities

    # Push
    if not push_folder(folder):
        print("::endgroup::")
        return False

    print("::endgroup::")
    return True


def main() -> int:
    changed_folders = get_changed_folders()
    changed_folders = ["basic-auth"]

    print(f"Detected changes in folders: {', '.join(changed_folders)}")

    failed = []

    for folder in changed_folders:
        if not folder_pipeline(folder):
            failed.append(folder)

    if len(failed) != 0:
        gh_error(f"The following images failed to build: {', '.join(failed)}")
        return 1

    print("Successfully built all images!")
    return 0


if __name__ == "__main__":
    exit(main())
