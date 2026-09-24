"""
Resolve a Julia version specification using the official versions.json:

    resolve_version.py 1        # the latest minor release, e.g. `1.13`
    resolve_version.py rc       # the latest release or release candidate, e.g. `1.14.0-rc1`
    resolve_version.py beta     # the same, but also considering betas
    resolve_version.py alpha    # the same, but also considering alphas and betas

The prerelease channels follow juliaup's semantics.  Only the Python standard library
is used, so that this works with whatever `python3` the agent has.
"""

import json
import re
import sys
import urllib.request

VERSIONS_URL = "https://julialang-s3.julialang.org/bin/versions.json"

# Prerelease stages, from least to most stable; `None` denotes a release.
STAGE_RANKS = {"alpha": 0, "beta": 1, "rc": 2, None: 3}

# Each channel considers releases and prereleases down to the stage of the same name.
CHANNELS = ("alpha", "beta", "rc")

VERSION_REGEX = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta|rc)(\d+))?")


class ResolveError(Exception):
    pass


def version_key(version):
    """
    Parse a version like `1.2.3` or `1.2.3-rc1` into a tuple that sorts by version number
    first, and by stability second.  Returns `None` for versions we do not understand.
    """
    match = VERSION_REGEX.fullmatch(version)
    if match is None:
        return None
    major, minor, patch, stage, number = match.groups()
    return (int(major), int(minor), int(patch), STAGE_RANKS[stage], int(number or 0))


def resolve(spec, catalog):
    """Resolve `spec` against `catalog`, the parsed contents of versions.json."""
    keys = {}
    for version in catalog:
        key = version_key(version)
        if key is not None:
            keys[version] = key

    if spec in CHANNELS:
        min_rank = STAGE_RANKS[spec]
        candidates = [v for v, key in keys.items() if key[3] >= min_rank]
        if not candidates:
            raise ResolveError(f"no release found for channel '{spec}'")
        return max(candidates, key=keys.get)

    if re.fullmatch(r"\d+", spec):
        major = int(spec)
        minors = [key[1] for v, key in keys.items()
                  if key[0] == major and catalog[v].get("stable", False)]
        if not minors:
            raise ResolveError(f"no stable release found for Julia {major}")
        return f"{major}.{max(minors)}"

    raise ValueError(f"unsupported version specification '{spec}'")


def download_catalog(url=VERSIONS_URL, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        catalog = json.loads(response.read().decode("utf-8"))
    if not isinstance(catalog, dict):
        raise ValueError("unexpected contents")
    return catalog


def main(argv):
    if len(argv) != 2:
        print(f"usage: {argv[0]} <major version | alpha | beta | rc>", file=sys.stderr)
        return 2
    spec = argv[1]
    if not (spec in CHANNELS or re.fullmatch(r"\d+", spec)):
        print(f"error: unsupported version specification '{spec}'", file=sys.stderr)
        return 2

    try:
        catalog = download_catalog()
    except (OSError, ValueError) as e:
        print(f"error: could not download {VERSIONS_URL}: {e}", file=sys.stderr)
        return 1

    try:
        print(resolve(spec, catalog))
    except ResolveError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
