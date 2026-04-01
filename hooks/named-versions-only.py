import json
import re
import sys
import urllib.request


class SimpleVersion:
    """
    A simple Julia version parser using only the Python standard library.

    Supported version formats:
        - "X.Y.Z"
        - "X.Y.Z-alphaN"
        - "X.Y.Z-betaN"
        - "X.Y.Z-rcN"

    Comparison is done with three stable sorts:
        1. suffix number
        2. suffix kind
        3. version number

    This makes the version number the most important piece of information,
    while still preferring stable releases over rcs, rcs over betas, and
    betas over alphas when the numeric version is the same.
    """

    def __init__(self, version_string):
        self.version_string = version_string
        match = re.match(
            r"^(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta|rc)(\d+))?$",
            version_string,
        )
        if not match:
            raise ValueError(f"Invalid version string: {version_string}")

        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.micro = int(match.group(3))
        self.suffix_kind = match.group(4)
        self.suffix_number = int(match.group(5)) if match.group(5) else 0

    def version_number_key(self):
        return (self.major, self.minor, self.micro)

    def suffix_kind_key(self):
        if self.suffix_kind is None:
            return 3
        if self.suffix_kind == "rc":
            return 2
        if self.suffix_kind == "beta":
            return 1
        if self.suffix_kind == "alpha":
            return 0
        raise ValueError(f"Invalid suffix kind: {self.suffix_kind}")

    def __str__(self):
        return self.version_string


def download_versions_json(url="https://julialang-s3.julialang.org/bin/versions.json"):
    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request).read()
    parsed_json = json.loads(response.decode("utf-8"))
    return parsed_json


def get_all_supported_versions(parsed_json):
    versions = []
    for version_string in parsed_json.keys():
        try:
            versions.append(SimpleVersion(version_string))
        except ValueError:
            continue
    return versions


def is_admissible(version_obj, requested_channel):
    if requested_channel == "alpha":
        return True
    if requested_channel == "beta":
        return version_obj.suffix_kind in (None, "rc", "beta")
    if requested_channel == "rc":
        return version_obj.suffix_kind in (None, "rc")
    raise Exception("the named version must be one of: alpha, beta, rc")


def order_versions_by_seniority(versions_list):
    ordered_versions = list(versions_list)
    ordered_versions.sort(key=lambda version: version.suffix_number)
    ordered_versions.sort(key=lambda version: version.suffix_kind_key())
    ordered_versions.sort(key=lambda version: version.version_number_key())
    return ordered_versions


def select_latest_named_version(parsed_json, requested_channel):
    versions = get_all_supported_versions(parsed_json)
    admissible_versions = [
        version for version in versions if is_admissible(version, requested_channel)
    ]
    if not admissible_versions:
        raise Exception("could not find a release matching the requested named version")

    ordered_versions = order_versions_by_seniority(admissible_versions)
    return ordered_versions[-1]


def _main(requested_channel):
    if requested_channel not in ("alpha", "beta", "rc"):
        raise Exception("the named version must be one of: alpha, beta, rc")
    parsed_json = download_versions_json()
    selected_version = select_latest_named_version(parsed_json, requested_channel)
    return selected_version


def main():
    if len(sys.argv) < 2:
        raise Exception(
            "the named version must be passed as the first positional command line argument"
        )
    requested_channel = sys.argv[1]
    selected_version = _main(requested_channel)
    print(selected_version)
    return None


if __name__ == "__main__":
    main()
