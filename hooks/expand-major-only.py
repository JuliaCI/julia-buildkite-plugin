import distutils.version
import json
import sys
import urllib.request

distutils.version.StrictVersion

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
    stable_versions = [distutils.version.StrictVersion(s) for s in stable_version_strings_unique]
    stable_versions.sort()
    return stable_versions

def get_major(version):
    return version.version[0]

def get_minor(version):
    return version.version[1]

def get_patch(version):
    return version.version[2]

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
