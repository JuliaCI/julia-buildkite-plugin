import json
import re
import sys
import urllib.request

class SimpleVersion:
    """
    A simple version class using only the Python standard library.

    This class is intended as a minimal replacement for standard library components
    such as distutils.version.StrictVersion, supporting only a subset of versioning features.

    Supported version format:
        - Version strings must be in the form "X.Y.Z", where X, Y, and Z are integers.
        - Example: "1.9.3"
        - No support for pre-releases, post-releases, alpha/beta/rc tags, or other PEP 440 features.

    Comparison behavior:
        - Versions are compared lexicographically by (major, minor, micro) components.
        - Only equality and less-than comparisons are implemented.

    Limitations:
        - Only the "X.Y.Z" format is accepted; other formats will raise ValueError.
        - Does not support version strings with fewer or more than three components.
        - Does not support non-numeric version parts.
        - Not a drop-in replacement for distutils.version.StrictVersion or packaging.version.Version.
    """
    def __init__(self, version_string):
        self.version_string = version_string
        # Parse version string like "1.9.3" into components
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version_string)
        if not match:
            raise ValueError(f"Invalid version string: {version_string}")
        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.micro = int(match.group(3))

    def __lt__(self, other):
        if not isinstance(other, SimpleVersion):
            return NotImplemented
        return (self.major, self.minor, self.micro) < (other.major, other.minor, other.micro)

    def __eq__(self, other):
        if not isinstance(other, SimpleVersion):
            return NotImplemented
        return (self.major, self.minor, self.micro) == (other.major, other.minor, other.micro)

    def __str__(self):
        return self.version_string

def download_versions_json(url = "https://julialang-s3.julialang.org/bin/versions.json"):
    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request).read()
    parsed_json = json.loads(response.decode('utf-8'))
    return parsed_json

def get_stable_versions(parsed_json):
    stable_version_strings = []
    for key in parsed_json.keys():
        version = parsed_json[key]
        if "stable" in version.keys():
            is_stable = version["stable"]
            if is_stable:
                stable_version_strings.append(key)
    stable_version_strings_unique = list(set(stable_version_strings))
    stable_versions = [SimpleVersion(s) for s in stable_version_strings_unique]
    stable_versions.sort()
    return stable_versions

def get_major(version_obj):
    return version_obj.major

def get_minor(version_obj):
    return version_obj.minor

def get_patch(version_obj):
    return version_obj.micro

def get_highest_minor_matching_major(versions_list, major):
    all_majors = [get_major(v) for v in versions_list]
    all_minors = [get_minor(v) for v in versions_list]
    matching_minors = []
    for i in range(len(versions_list)):
        ith_major = all_majors[i]
        ith_minor = all_minors[i]
        if ith_major == major:
            matching_minors.append(ith_minor)
    if not matching_minors:
        raise Exception("could not find a stable release with the required major version")
    return max(matching_minors)

def _main(major):
    if (not isinstance(major, int)):
        raise Exception("major must be an integer")
    parsed_json = download_versions_json()
    stable_versions = get_stable_versions(parsed_json)
    highest_matching_minor = get_highest_minor_matching_major(stable_versions, major)
    return highest_matching_minor

def main():
    if len(sys.argv) < 2:
        raise Exception("the major version number must be passed as the first positional command line argument")
    major = int(sys.argv[1])
    highest_matching_minor = _main(major)
    print(major, ".", highest_matching_minor, sep = "")
    return None

if __name__ == "__main__":
    main()
