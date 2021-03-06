#!/usr/bin/env python3

"""
Builds Docker images found in github.com/slateci/docker-images.

This script assumes the following:
1. pyyaml Python package is installed.
2. hadolint is installed and on $PATH.
4. Docker Buildx is configured to be used by default.
5. `docker login` has been called for each registry.
"""

import argparse
import datetime
import json
import re
import subprocess
from contextlib import contextmanager
from functools import partial
from os import getenv, path
from pathlib import Path
from sys import stderr, stdout
from typing import Any, Dict, List, NamedTuple, Optional, Set, cast

import requests
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

BUILD_FOLDERS_FILE = "build_folders.txt"

LABEL_SCHEMA_FIELDS = ["name", "description", "maintainer", "usage", "url", "version"]
SLATE_FIELDS = ["maintainer"]


class Metadata:
    name: str
    version: str
    description: Optional[str]
    maintainer: Optional[str]
    usage: Optional[str]
    url: Optional[str]
    tags: List[str]

    def __init__(
        self,
        name: str,
        version: str,
        description: Optional[str] = None,
        maintainer: Optional[str] = None,
        usage: Optional[str] = None,
        url: Optional[str] = None,
        tags: List[str] = [],
    ) -> None:
        if not isinstance(name, str):
            raise RuntimeError("'name' is not of type str.")
        if not isinstance(version, str):
            raise RuntimeError("'version' is not of type str.")
        if not (description is None or isinstance(description, str)):
            raise RuntimeError("'description' is not of type Optional[str].")
        if not (maintainer is None or isinstance(maintainer, str)):
            raise RuntimeError("'maintainer' is not of type Optional[str].")
        if not (usage is None or isinstance(usage, str)):
            raise RuntimeError("'usage' is not of type Optional[str].")
        if not (url is None or isinstance(url, str)):
            raise RuntimeError("'url' is not of type Optional[str].")
        if not (isinstance(tags, list) and all(isinstance(i, str) for i in tags)):
            raise RuntimeError("'tags' is not of type List[str].")

        if not re.match(r"^\d+[.]\d+[.]\d+$", version):
            raise RuntimeError("'version' must be of semver form (e.g. 1.0.0).")

        self.name = name
        self.version = version
        self.description = description
        self.maintainer = maintainer
        self.usage = usage
        self.url = url
        self.tags = tags


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
ENABLE_GHA_PRINTING = True


@contextmanager
def disable_gha_printing():
    # TODO: refactor project to use Result types to avoid having to use this hack
    global ENABLE_GHA_PRINTING
    tmp = ENABLE_GHA_PRINTING
    ENABLE_GHA_PRINTING = False
    yield
    ENABLE_GHA_PRINTING = tmp


@contextmanager
def gha_group(group_name: str):
    print("::group::" + group_name)
    yield
    print("::endgroup::")


def gha_error(msg: str) -> None:
    if ENABLE_GHA_PRINTING:
        print("::error::" + msg)


def gha_warning(msg: str) -> None:
    if ENABLE_GHA_PRINTING:
        print("::warning::" + msg)


def get_build_folders() -> Set[str]:
    with open(BUILD_FOLDERS_FILE) as f:
        return set(f.read().splitlines())


def get_changed_folders(from_commit: str, to_commit: str) -> Optional[Set[str]]:
    """Returns a set of folder names that have changes between the given
    commits."""
    folders = get_build_folders()

    # Git pushes can include multiple commits, thus
    # `git diff --name-only HEAD` is insufficient.
    git_diff = subprocess.run(
        ["git", "diff", "--name-only", f"{from_commit}..{to_commit}"],
        capture_output=True,
    )

    # git diff could have failed for a number of reasons:
    # 1. We have a shallow repo clone (default for Github Actions)
    # 2. We force pushed likely causing from_commit to become orphaned.
    #    Orphaned commits are not pulled down during git fetch / git pull, thus
    #    git diff may not have a record of that commit.
    #
    # Github should have the commits (orphaned or not, Github doesn't
    # aggressively GC orphaned commits), thus we can query Github directly for
    # the diff information.
    if git_diff.returncode != 0:
        print("git diff failed locally, trying diff with Github API...")

        github_token = getenv("GITHUB_TOKEN")
        if github_token is None:
            gha_error("Environmental variable GITHUB_TOKEN is not set!")
            return None

        compare_endpoint = getenv("GITHUB_COMPARE_ENDPOINT")
        if compare_endpoint is None:
            gha_error("Environmental variable GITHUB_COMPARE_ENDPOINT is not set!")
            return None

        # Github compare will return different files depending on the order of
        # commits due to how it does ancestor search. Check both orders for a
        # more complete view of the diff.
        folder_list = set()
        for base, head in [(from_commit, to_commit), (to_commit, from_commit)]:
            r = requests.get(
                compare_endpoint.format(base=base, head=head),
                # Username isn't required for personal access token.
                auth=("", github_token),
            )

            if r.status_code != 200:
                gha_error("Failed to query Github for compare info: " + r.text)
                return None

            try:
                payload = json.loads(r.text)
            except json.JSONDecodeError as e:
                gha_error("Failed to convert payload to JSON: " + str(e))
                return None

            if "files" not in payload:
                gha_error("Did not find files field in payload!")
                return None

            folder_list |= set(
                map(lambda x: Path(x["filename"]).parts[0], payload["files"])
            )
    else:
        folder_list = set(
            map(lambda x: x.split("/")[0], git_diff.stdout.decode().splitlines())
        )

    # Return only the folders we care about using set AND.
    return folder_list & folders


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
            # Allow for both space delimited and comma delimited folder lists.
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
    metadata: Metadata,
    existence_t: List[str],
    cache_t: List[str],
    push_t: List[str],
    save_t: List[str],
) -> Tags:
    local_t = metadata.name + ":" + metadata.version

    # Expand 'tags[]' field.
    def expand_tags(tags: List[str]):
        for tag in tags:
            if "{tags[]}" in tag:
                for recur in expand_tags(
                    [
                        # Expand ONLY the first instance of {tags[]}
                        # and keep all other format blocks untouched.
                        # only a little cursed
                        tag.replace("{", "{{")
                        .replace("}", "}}")
                        .replace("{{tags[]}}", "{t}", 1)
                        .format(t=t)
                        for t in metadata.tags
                    ]
                ):
                    yield recur

            else:
                yield tag

    existence_t = list(expand_tags(existence_t))
    cache_t = list(expand_tags(cache_t))
    push_t = list(expand_tags(push_t))
    save_t = list(expand_tags(save_t))

    # Build with any tag that should be saved or pushed.
    build_t = set(push_t) | set(save_t) | {local_t}

    return Tags(
        local=local_t,
        existence=[
            t.format(name=metadata.name, version=metadata.version) for t in existence_t
        ],
        cache=[t.format(name=metadata.name, version=metadata.version) for t in cache_t],
        build=[t.format(name=metadata.name, version=metadata.version) for t in build_t],
        push=[t.format(name=metadata.name, version=metadata.version) for t in push_t],
        save=[t.format(name=metadata.name, version=metadata.version) for t in save_t],
    )


### Prebuild Checks ###
def check_required_files(folder: str) -> bool:
    if not path.isfile(f"{folder}/Dockerfile"):
        gha_error("Dockerfile not found!")
        return False

    if not path.isfile(f"{folder}/metadata.yml"):
        gha_error("metadata.yml not found!")
        return False

    return True


def get_metadata(folder: str) -> Optional[Metadata]:
    try:
        with open(f"{folder}/metadata.yml") as f:
            metadata = yaml.load(f.read(), Loader=Loader)
    except Exception as e:
        gha_error(f"Failed to read metadata.yml: {e}")
        return None

    if not isinstance(metadata, dict):
        gha_error("Unexpected metadata.yml format!")
        return None

    metadata = cast(Dict[str, Any], metadata)
    try:
        md_obj = Metadata(**metadata)
    except RuntimeError as e:
        gha_error(f"Metadata error: {e.args[0]}")
        return None

    return md_obj


def populate_claimed_tags(folders: Set[str]) -> Dict[str, str]:
    """Populate claimed_tags with tags from folders that have not changed,
    used to sanity check that two folders don't use the same tag."""
    # disable gh_error temporarily to ignore folder errors
    with disable_gha_printing():
        claimed_tags: Dict[str, str] = {}
        for folder in folders:
            if not check_required_files(folder):
                continue

            metadata = get_metadata(folder)
            if metadata is None:
                continue

            for t in [metadata.version] + metadata.tags:
                claimed_tags[metadata.name + ":" + t] = folder

        return claimed_tags


def check_tag_collision(
    claimed_tags: Dict[str, str],
    metadata: Metadata,
    folder: str,
) -> bool:
    """Return False if a tag in to_claim_tags exists in claimed_tags, True otherwise.
    Side effect: updates claimed_tags"""
    for tag in [metadata.version] + metadata.tags:
        t = metadata.name + ":" + tag

        if t in claimed_tags:
            gha_error(
                f"Tag '{t}' is used by the image in folder {claimed_tags[t]}, refusing to continue due to tag collision..."
            )
            return False

        claimed_tags[t] = folder

    return True


def check_tags_pushed(tags: List[str]) -> bool:
    for t in tags:
        check = subprocess.run(
            ["docker", "manifest", "inspect", t], capture_output=True
        )

        if check.returncode == 0:
            gha_error(f"{t} exists, stopping...")
            print(
                "Overriding existing tags of a container is _dangerous_ "
                "and should be avoided if possible. We recommend incrementing "
                "the version number in metadata.yml instead or ignoring this "
                "error if these commits do not substantially change the container "
                "(e.g. adding whitespace / comments to files). If you know what "
                "you are doing, you can force a build/push from the Actions tab."
            )
            return False

    return True


### Lint ###
def lint_folder(folder: str, fail_level: str) -> bool:
    print(">>>> Lint Dockerfile <<<<")

    lint_output = subprocess.run(
        ["hadolint", "--no-fail", "Dockerfile"], capture_output=True, cwd=folder
    )

    lint_stdout = lint_output.stdout.decode().strip()
    print(lint_stdout)

    if lint_output.returncode != 0:
        gha_error("Failed to lint Dockerfile!")
        return False

    fail_level_map = {
        "STYLE": ["style", "info", "warning", "error"],
        "INFO": ["info", "warning", "error"],
        "WARNING": ["warning", "error"],
        "ERROR": ["error"],
    }

    if any(lvl in lint_stdout for lvl in fail_level_map[fail_level]):
        gha_error("Dockerfile failed linter test!")
        return False

    print(">> Lint successful! <<")

    return True


### Build ###
def build_folder(
    folder: str, metadata: Metadata, tags: List[str], cache_from: List[str]
) -> bool:
    print(">>>> Build Image <<<<")
    print("Building tags: ", tags)
    print("Caching from: ", cache_from)

    labels = {}
    for field in LABEL_SCHEMA_FIELDS:
        if getattr(metadata, field) is not None:
            labels[f"org.label-schema.{field}"] = getattr(metadata, field)

    for field in SLATE_FIELDS:
        if getattr(metadata, field) is not None:
            labels[f"io.slateci.{field}"] = getattr(metadata, field)

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

    cache_from_flags = [f"--cache-from=type=registry,ref={t}" for t in cache_from]

    # Clean Docker image cache. This is necessary as we could potentially build
    # multiple images in a single go and exhaust storage space on the runner.
    cache_clean = subprocess.run(
        ["docker", "buildx", "prune", "-a", "-f"], capture_output=True
    )

    if cache_clean.returncode != 0:
        gha_error("Failed to clean build cache!")
        return False

    image_clean = subprocess.run(
        ["docker", "image", "prune", "-f"], capture_output=True
    )

    if image_clean.returncode != 0:
        gha_error("Failed to prune images!")
        return False

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
        gha_error("Failed to build!")
        return False

    print(">> Successfully built! <<")
    return True


### Scan for Vulnerabilities ###
def dockle_scan(folder:str, tag: str, fail_level: str) -> bool:
    print(">>>> Dockle Scan <<<<")

    scan_output = subprocess.run(
        ["dockle", "--exit-code", "1", "--exit-level", fail_level.lower(), tag], cwd=folder
    )

    if scan_output.returncode != 0:
        gha_error("Image failed Dockle scan!")
        return False

    print(">> Dockle Scan successful! <<")

    return True


def trivy_scan(folder:str, tag: str, fail_level: str) -> bool:
    print(">>>> Trivy Scan <<<<")

    scan_output = subprocess.run(
        ["trivy", "i", "--ignore-unfixed", "--light", tag], capture_output=True, cwd=folder
    )

    scan_stdout = scan_output.stdout.decode().strip()
    print(scan_stdout)

    if scan_output.returncode != 0:
        gha_error("Failed to perform Trivy scan!")
        return False

    fail_level_map = {
        "LOW": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        "MEDIUM": ["MEDIUM", "HIGH", "CRITICAL"],
        "HIGH": ["HIGH", "CRITICAL"],
        "CRITICAL": ["CRITICAL"],
    }

    # A hack to get just the table so the summary at the top doesn't
    # trip a false positive.
    # TODO: find a more elegant solution for this
    scan_table = scan_stdout[scan_stdout.find("+--") :]

    if any(lvl in scan_table for lvl in fail_level_map[fail_level]):
        gha_error("Image failed Trivy scan!")
        return False

    print(">> Trivy Scan successful! <<")

    return True


### Push ###
def push_tags(tags: List[str]) -> bool:
    print(">>>> Push Image <<<<")
    print("Pushing tags: ", tags)

    for t in tags:
        push_output = subprocess.run(["docker", "push", t], stdout=stdout)

        if push_output.returncode != 0:
            gha_error(f"Failed to push {t}!")
            return False

    print(">> Successfully pushed! <<")
    return True


### Save Image ###
def save_tags(save_to: str, tags: List[str]) -> bool:
    print(">>>> Save Image <<<<")

    loc = Path(save_to)

    if loc.suffix != ".tar":
        gha_error("Save location must end in .tar!")
        return False

    if not loc.parent.exists():
        loc.parent.mkdir()

    save_img = subprocess.run(["docker", "save", "-o", str(loc)] + tags, stdout=stdout)

    if save_img.returncode != 0:
        gha_error(f"Failed to save images in {loc}!")
        return False

    print(">> Successfully Saved Image! <<")
    return True


### Main Functions ###
def pipeline(args: argparse.Namespace) -> int:
    # For debugging argparse.
    # print("Calling 'build.py pipeline' with args: " + str(args))

    changed_folders = get_changed_folders(args.from_commit, args.to_commit)

    if changed_folders is None:
        return 1

    print(f"Detected changes in folders: {', '.join(changed_folders)}")

    failed = []

    claimed_tags = populate_claimed_tags(get_build_folders() - changed_folders)

    for folder in changed_folders:
        with gha_group(folder):
            if not check_required_files(folder):
                failed.append(folder)
                continue

            metadata = get_metadata(folder)
            if metadata is None:
                failed.append(folder)
                continue

            tags = get_tags(
                metadata,
                args.check_existence_of,
                args.cache_from,
                args.push_tags,
                args.save_tags,
            )

            if not (
                (check_tag_collision(claimed_tags, metadata, folder))
                and (check_tags_pushed(tags.existence))
                and lint_folder(folder, args.lint_fail_level)
                and build_folder(
                    folder,
                    metadata,
                    tags.build,
                    tags.cache,
                )
                and dockle_scan(folder, tags.local, args.dockle_fail_level )
                and trivy_scan(folder, tags.local, args.trivy_fail_level)
                and (
                    save_tags(args.save_images_to, tags.save)
                    if args.save_tags
                    else True
                )
                and (push_tags(tags.push) if args.push_tags else True)
            ):
                failed.append(folder)
                continue

    if len(failed) != 0:
        gha_error(f"The following images failed to build: {', '.join(failed)}")
        return 1

    print("Successfully built all images!")
    return 0


def lint(args: argparse.Namespace) -> int:
    print("Calling 'build.py lint' with args: " + str(args))

    folders = parse_folders_args(args)
    failed = []

    for folder in folders:
        with gha_group(folder):
            if not (
                check_required_files(folder)
                # check that the metadata file is valid
                and get_metadata(folder)
                and lint_folder(folder, args.fail_level)
            ):
                failed.append(folder)
                continue

    if len(failed) != 0:
        gha_error(f"The following images failed to lint: {', '.join(failed)}")
        return 1

    print("Successfully linted all images!")
    return 0


def force_build(args: argparse.Namespace) -> int:
    print("Calling 'build.py force-build' with args: " + str(args))

    folders = parse_folders_args(args)
    failed = []

    claimed_tags = populate_claimed_tags(get_build_folders() - folders)

    for folder in folders:
        with gha_group(folder):
            if not check_required_files(folder):
                failed.append(folder)
                continue

            metadata = get_metadata(folder)
            if metadata is None:
                failed.append(folder)
                continue

            tags = get_tags(
                metadata,
                [],
                args.cache_from,
                args.push_tags,
                args.save_tags,
            )

            if not (
                check_tag_collision(claimed_tags, metadata, folder)
                and build_folder(folder, metadata, tags.build, tags.cache)
                and (
                    save_tags(args.save_images_to, tags.save)
                    if args.save_tags
                    else True
                )
                and (push_tags(tags.push) if args.push_tags else True)
            ):
                failed.append(folder)
                continue

    if len(failed) != 0:
        gha_error(f"The following images failed to build: {', '.join(failed)}")
        return 1

    print("Successfully built all images!")
    return 0


def get_changed(args: argparse.Namespace) -> int:
    changed_folders = get_changed_folders(args.from_commit, args.to_commit)

    if changed_folders is None:
        return 1

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
        "Lint, build, and push/save folders that have changed between specified commits.\n\n"
        "Tag related flags can use {name}, {version}, and {tags[]}, as placeholders. "
        "The latter two will expand to each tag in the list.\n"
        "Ex: if name = 'foobar' and tags = ['latest', 'latest3'] then `--push-tags ghcr.io/slateci/{name}:{tags[]}` will push the tags 'ghcr.io/slateci/foobar:latest' and 'ghcr.io/slateci/foobar:latest3'.\n\n"
        "dockle performs basic vuln checks on the Docker image. "
        "trivy performs sophisticated vuln checks on the Docker image using vulnerability databases. \n\n"
        "`git diff` will first be used to diff between from_commit and to_commit. "
        "In the event `git diff` fails (e.g. if from_commit doesn't exist locally), the Github API will be used with $GITHUB_TOKEN and $GITHUB_COMPARE_ENDPOINT (which should be of the form https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head} where {base} and {head} are left as is but the rest are filled in)."
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
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
pipeline_p.add_argument(
    "--lint-fail-level",
    choices=["STYLE", "INFO", "WARNING", "ERROR"],
    help="the level of error from hadolint to fail on, one of STYLE, INFO, WARNING, or ERROR (default ERROR)",
    metavar="LEVEL",
    default="ERROR",
)
pipeline_p.add_argument(
    "--dockle-fail-level",
    choices=["INFO", "WARN", "FATAL"],
    help="the level of error from dockle to fail on, one of INFO, WARN, or FATAL (default FATAL)",
    metavar="LEVEL",
    default="FATAL",
)
pipeline_p.add_argument(
    "--trivy-fail-level",
    choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
    help="the level of error from trivy to fail on, one of LOW, MEDIUM, HIGH, or CRITICAL (default CRITICAL)",
    metavar="LEVEL",
    default="CRITICAL",
)
pipeline_p.set_defaults(func=pipeline)

lint_p = subparsers.add_parser(
    "lint", description="Lint specified folders.", help="Lint folders"
)
lint_p.add_argument(
    "folders", help="space and/or comma separated list of folders to lint", nargs="*"
)
lint_p.add_argument("--all", help="lint all folders", action="store_true")
lint_p.add_argument(
    "--fail-level",
    choices=["STYLE", "INFO", "WARNING", "ERROR"],
    help="the level of error from hadolint to fail on, one of STYLE, INFO, WARNING, or ERROR (default ERROR)",
    metavar="LEVEL",
    default="ERROR",
)
lint_p.set_defaults(func=lint)

force_build_p = subparsers.add_parser(
    "force-build",
    description=(
        "Force build and push/save specified folders (ignoring lint, version existence, and vulnerability errors).\n\n"
        "Tag related flags can use {name}, {version}, and {tags[]} as placeholders. "
        "The latter two will expand to each tag in the list.\n"
        "Ex: if name = 'foobar' and tags = ['latest', 'latest3'] then `--push-tags ghcr.io/slateci/{name}:{tags[]}` will push the tags 'ghcr.io/slateci/foobar:latest' and 'ghcr.io/slateci/foobar:latest3'.\n\n"
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
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
    description=(
        "Get a new-line delimited list of folders that have changed between commits. \n\n"
        "`git diff` will first be used to diff between from_commit and to_commit. "
        "In the event `git diff` fails (e.g. if from_commit doesn't exist locally), the Github API will be used with $GITHUB_TOKEN and $GITHUB_COMPARE_ENDPOINT (which should be of the form https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head} where {base} and {head} are left as is but the rest are filled in)."
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
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
