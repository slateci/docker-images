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

IMAGE_URL = "ghcr.io/slateci"

# TODO:
#   1. Check if the version being built already exists in the registry.
#   2. Add force build/push and lint/scan buttons.
#   3. Push images on non-stable branches (e.g. beta), and clean up those branches after they are merged.
#   4. Change detection should use commit _from last push_.
#   5. Add GH action cron job to check for vulnerabilities.

# Force print to flush each time it's called.
print = partial(print, flush=True)

### Helper Functions ###
# See https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions#grouping-log-lines
# for information about these ::keyword:: messages.
def gh_error(msg: str) -> None:
    print("::error::" + msg)


def gh_warning(msg: str) -> None:
    print("::warning::" + msg)


def get_changed_folders(from_commit: str, to_commit: str) -> Set[str]:
    # Get the list of folders we should be building.
    with open(BUILD_FOLDERS_FILE) as f:
        folders = set(f.read().splitlines())

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


def get_metadata(folder: str) -> Optional[Tuple[Dict[str, Any], List[str]]]:
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

    # TODO: add check for stable branch here
    return metadata, [
        f"{IMAGE_URL}/{metadata['name']}:{metadata['version']}",
        f"{IMAGE_URL}/{metadata['name']}:latest",
    ]


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
        subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True)
        .stdout.decode()
        .strip()
    )

    labels_flags = []
    for k, v in labels.items():
        labels_flags += ["--label", f"{k}={v}"]

    tag_flags = []
    for t in tags:
        tag_flags += ["--tag", t]

    # Pull image caches.
    build_output = subprocess.run(
        [
            "docker",
            "buildx",
            "build",
            ".",
            "--file",
            "Dockerfile",
            f"--cache-from=type=registry,ref={IMAGE_URL}/{metadata['name']}:latest",
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
def main_pipeline(folder: str) -> bool:
    print(f"::group::{folder}")

    # Use short circuiting to chain results (if only Python had monads).
    retval = False
    if (
        check_required_files(folder)
        and (mt_tuple := get_metadata(folder))
        # and lint_folder(folder)
        and build_folder(folder, *mt_tuple)
        # and scan_for_vulnerability(folder, mt_tuple[1])
        and push_folder(folder, mt_tuple[1])
    ):
        retval = True

    print("::endgroup::")
    return retval


parser = argparse.ArgumentParser(
    description="""
Builds Docker images for slateci/docker-images.
Only one mode's flags may be used.
Folders must be listed in build_folders.txt for any of these actions.
"""
)

commit_group = parser.add_argument_group(
    title="Build on Changes",
    description="""
Build any folder with changes between from-commit to to-commit.
""",
)
commit_group.add_argument(
    "--from-commit", help="commit SHA from which to search for changes (exclusive)"
)
commit_group.add_argument(
    "--to-commit", help="commit SHA to which to search for changes (inclusive)"
)


def main() -> int:
    args = parser.parse_args()

    if bool(args.from_commit) ^ bool(args.to_commit):
        parser.error("--from-commit and --to-commit must be given together")
        return 1

    changed_folders = get_changed_folders(args.from_commit, args.to_commit)

    print(f"Detected changes in folders: {', '.join(changed_folders)}")

    failed = []

    for folder in changed_folders:
        if not main_pipeline(folder):
            failed.append(folder)

    if len(failed) != 0:
        gh_error(f"The following images failed to build: {', '.join(failed)}")
        return 1

    print("Successfully built all images!")
    return 0


if __name__ == "__main__":
    exit(main())
