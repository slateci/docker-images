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
from pathlib import Path
from sys import stderr, stdout
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple, cast

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

BUILD_FOLDERS_FILE = "build_folders.txt"

LABEL_SCHEMA_FIELDS = ["name", "description", "maintainer", "usage", "url", "version"]
SLATE_FIELDS = ["maintainer"]


class Tags(NamedTuple):
    local: str
    existence: List[str]
    cache: List[str]
    build: List[str]
    push: List[str]
    save: List[str]


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


def parse_folders_args(args: argparse.Namespace) -> Set[str]:
    build_folders = get_build_folders()

    if args.all:
        if args.folders:
            print("Ignoring specified folders due to --all flag...", file=stderr)

        return build_folders
    else:
        folders = set()

        if not args.folders:
            print("No folders specified, doing nothing...", file=stderr)

        for f in args.folders:
            for ff in f.split(","):
                if ff not in build_folders:
                    print(
                        f"Skipping {ff} as it is not in {BUILD_FOLDERS_FILE}...",
                        file=stderr,
                    )
                else:
                    folders.add(ff)

        return folders


def get_tags(
    metadata: Dict[str, Any],
    existence_t: List[str],
    cache_t: List[str],
    push_t: List[str],
    save_t: List[str],
) -> Tags:
    local_t = metadata["name"] + ":" + metadata["version"]
    build_t = set(push_t) | set(save_t) | {local_t}

    return Tags(
        local=local_t,
        existence=[
            t.format(name=metadata["name"], version=metadata["version"])
            for t in existence_t
        ],
        cache=[
            t.format(name=metadata["name"], version=metadata["version"])
            for t in cache_t
        ],
        build=[
            t.format(name=metadata["name"], version=metadata["version"])
            for t in build_t
        ],
        push=[
            t.format(name=metadata["name"], version=metadata["version"]) for t in push_t
        ],
        save=[
            t.format(name=metadata["name"], version=metadata["version"]) for t in save_t
        ],
    )


### Prebuild Checks ###
def check_required_files(folder: str) -> bool:
    if not path.isfile(f"{folder}/Dockerfile"):
        gh_error("Dockerfile not found!")
        return False

    if not path.isfile(f"{folder}/metadata.yml"):
        gh_error("metadata.yml not found!")
        return False

    return True


def get_metadata(folder: str) -> Optional[Dict[str, Any]]:
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

    return metadata


def check_tags_exists(tags: List[str]) -> bool:
    for t in tags:
        check = subprocess.run(
            ["docker", "manifest", "inspect", t], capture_output=True
        )

        if check.returncode == 0:
            gh_error(f"{t} exists, stopping...")
            print(
                "Overriding existing tags of a container is _dangerous_ "
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
def build_folder(
    folder: str, metadata: Dict[str, Any], tags: List[str], cache_from: List[str]
) -> bool:
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

    cache_from_flags = [f"--cache-from=type=registry,ref={t}" for t in cache_from]

    labels_flags = []
    for k, v in labels.items():
        labels_flags += ["--label", f"{k}={v}"]

    tag_flags = []
    for t in tags:
        tag_flags += ["--tag", t]

    # Clean Docker image cache. This is necessary as we could potentially build
    # multiple images in a single go and exhaust storage space on the runner.
    cache_clean = subprocess.run(
        ["docker", "buildx", "prune", "-a", "-f"], stdout=stdout
    )

    if cache_clean.returncode != 0:
        gh_error("Failed to clean build cache!")
        return False

    image_clean = subprocess.run(["docker", "image", "prune", "-f"])

    if image_clean.returncode != 0:
        gh_error("Failed to prune images!")
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
            "--output=type=docker",
            "--cache-to=type=inline",
        ]
        + cache_from_flags
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
def scan_for_vulnerability(folder: str, tag: str) -> bool:
    print(">>>> Scan Image for Vulnerabilities <<<<")

    # TODO: use Dockle and Trivy here instead
    scan_output = subprocess.run(
        ["docker", "scan", f"{tag}"],
        stdout=stdout,
        cwd=folder,
    )

    if scan_output.returncode != 0:
        gh_error("Image failed vulnerability scan!")
        return False

    print(">> Image vulnerability scan came back clean! <<")
    return True


### Push ###
def push_tags(tags: List[str]) -> bool:
    print(">>>> Push Image <<<<")

    for t in tags:
        push_output = subprocess.run(["docker", "push", t], stdout=stdout)

        if push_output.returncode != 0:
            gh_error(f"Failed to push {t}!")
            return False

    print(">> Successfully pushed! <<")
    return True


### Save Image ###
def save_tags(save_to: str, tags: List[str]) -> bool:
    print(">>>> Save Image <<<<")

    loc = Path(save_to)

    if loc.suffix != ".tar":
        gh_error("Save location must end in .tar!")
        return False

    if not loc.parent.exists():
        loc.parent.mkdir()

    save_img = subprocess.run(["docker", "save", "-o", str(loc)] + tags, stdout=stdout)

    if save_img.returncode != 0:
        gh_error(f"Failed to save images in {loc}!")
        return False

    print(">> Successfully Saved Image! <<")
    return True


### Main Functions ###
def pipeline(args: argparse.Namespace) -> int:
    print("Calling 'build.py pipeline' with args: " + str(args))

    changed_folders = get_changed_folders(args.from_commit, args.to_commit)

    print(f"Detected changes in folders: {', '.join(changed_folders)}")

    failed = []

    for folder in changed_folders:
        print(f"::group::{folder}")

        if not check_required_files(folder):
            failed.append(folder)
            print("::endgroup::")
            continue

        metadata = get_metadata(folder)
        if metadata is None:
            failed.append(folder)
            print("::endgroup::")
            continue

        tags = get_tags(
            metadata,
            args.check_existence_of,
            args.cache_from,
            args.push_tags,
            args.save_tags,
        )

        if not (
            not (check_tags_exists(tags.existence))
            and lint_folder(folder)
            and build_folder(
                folder,
                metadata,
                tags.build,
                tags.cache,
            )
            # and scan_for_vulnerability(folder, tags.local)
            and (save_tags(args.save_images_to, tags.save) if args.save_tags else True)
            and (push_tags(tags.push) if args.push_tags else True)
        ):
            failed.append(folder)

        print("::endgroup::")

    if len(failed) != 0:
        gh_error(f"The following images failed to build: {', '.join(failed)}")
        return 1

    print("Successfully built all images!")
    return 0


def lint(args: argparse.Namespace) -> int:
    print("Calling 'build.py lint' with args: " + str(args))

    folders = parse_folders_args(args)
    failed = []

    for folder in folders:
        print(f"::group::{folder}")

        if not (
            check_required_files(folder)
            # check that the metadata file is valid
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


def force_build(args: argparse.Namespace) -> int:
    print("Calling 'build.py force-build' with args: " + str(args))

    folders = parse_folders_args(args)
    failed = []

    for folder in folders:
        print(f"::group::{folder}")

        if not check_required_files(folder):
            failed.append(folder)
            print("::endgroup::")
            continue

        metadata = get_metadata(folder)
        if metadata is None:
            failed.append(folder)
            print("::endgroup::")
            continue

        tags = get_tags(
            metadata,
            [],
            args.cache_from,
            args.push_tags,
            args.save_tags,
        )

        if not (
            build_folder(folder, metadata, tags.build, tags.cache)
            and (save_tags(args.save_images_to, tags.save) if args.save_tags else True)
            and (push_tags(tags.push) if args.push_tags else True)
        ):
            failed.append(folder)

        print("::endgroup::")

    if len(failed) != 0:
        gh_error(f"The following images failed to build: {', '.join(failed)}")
        return 1

    print("Successfully built all images!")
    return 0


def get_changed(args: argparse.Namespace) -> int:
    changed_folders = get_changed_folders(args.from_commit, args.to_commit)

    print("\n".join(changed_folders))
    return 0


parser = argparse.ArgumentParser(
    description="""
Builds Docker images for slateci/docker-images.
Folders must be listed in build_folders.txt for any of these actions.
"""
)
subparsers = parser.add_subparsers()

pipeline_p = subparsers.add_parser(
    "pipeline",
    description=(
        "Lint, build, and push/save folders that have changed between specified commits. "
        "Tag related flags can use {name} and {version} as placeholders. "
        "Ex: --push-tags ghcr.io/slateci/{name}:{version}"
    ),
    help="Lint, build, and push/save folders that have changed between specified commits",
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
    "--check-existence-of",
    help="fail if these image tags exists",
    nargs="*",
    metavar="TAG",
    default=[],
)
pipeline_p.add_argument(
    "--cache-from",
    help="image tags to cache builds from",
    nargs="*",
    metavar="TAG",
    default=[],
)
pipeline_p.add_argument(
    "--push-tags", help="image tags to push", nargs="*", metavar="TAG", default=[]
)
pipeline_p.add_argument(
    "--save-tags",
    help="image tags to save locally",
    nargs="*",
    metavar="TAG",
    default=[],
)
pipeline_p.add_argument(
    "--save-images-to",
    type=str,
    help="save tags (if any) to FILE (default: _save/images.tar)",
    metavar="FILE",
    default="_save/images.tar",
)
pipeline_p.set_defaults(func=pipeline)

lint_p = subparsers.add_parser(
    "lint", description="Lint specified folders.", help="Lint folders"
)
lint_p.add_argument(
    "folders", help="space and/or comma separated list of folders to lint", nargs="*"
)
lint_p.add_argument("--all", help="lint all folders", action="store_true")
lint_p.set_defaults(func=lint)

force_build_p = subparsers.add_parser(
    "force-build",
    description=(
        "Force build and push/save specified folders (ignoring lint, version existence, and vulnerability errors). "
        "Tag related flags can use {name} and {version} as placeholders. "
        "Ex: --push-tags ghcr.io/slateci/{name}:{version}"
    ),
    help="Force build and push/save specified folders (ignoring lint, version existence, and vulnerability errors)",
)
force_build_p.add_argument(
    "folders",
    help="space and/or comma separated list of folders to force build",
    nargs="*",
)
force_build_p.add_argument(
    "--all", help="force build and push/save all folders", action="store_true"
)
force_build_p.add_argument(
    "--cache-from",
    help="image tags to cache builds from",
    nargs="*",
    metavar="TAG",
    default=[],
)
force_build_p.add_argument(
    "--push-tags", help="image tags to push", nargs="*", metavar="TAG", default=[]
)
force_build_p.add_argument(
    "--save-tags",
    help="image tags to save locally",
    nargs="*",
    metavar="TAG",
    default=[],
)
force_build_p.add_argument(
    "--save-images-to",
    type=str,
    help="save tags (if any) to FILE (default: _save/images.tar)",
    metavar="FILE",
    default="_save/images.tar",
)
force_build_p.set_defaults(func=force_build)

get_changed_p = subparsers.add_parser(
    "get-changed",
    description="Get a new-line delimited list of folders that have changed between commits",
    help="Get a list of folders that have changed between commits.",
)
get_changed_p.add_argument(
    "from_commit",
    type=str,
    help="commit SHA from which to search for changes (exclusive)",
)
get_changed_p.add_argument(
    "to_commit",
    type=str,
    help="commit SHA to which to search for changes (inclusive)",
)
get_changed_p.set_defaults(func=get_changed)

if __name__ == "__main__":
    args = parser.parse_args()
    exit(args.func(args))
