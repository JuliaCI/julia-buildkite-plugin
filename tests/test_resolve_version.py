import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import resolve_version
from resolve_version import ResolveError, resolve, version_key


def catalog(*stable, prerelease=()):
    """Build a minimal versions.json catalog."""
    entries = {v: {"stable": True, "files": []} for v in stable}
    entries.update({v: {"stable": False, "files": []} for v in prerelease})
    return entries


class TestVersionKey(unittest.TestCase):
    def test_ordering(self):
        ordered = ["1.12.5", "1.13.0-alpha1", "1.13.0-alpha2", "1.13.0-beta1",
                   "1.13.0-rc2", "1.13.0-rc10", "1.13.0", "1.13.1", "1.14.0-alpha1"]
        self.assertEqual(sorted(reversed(ordered), key=version_key), ordered)

    def test_unsupported(self):
        for version in ["1.13", "1.13.0-DEV", "0.7.0-alpha", "0.6.0-pre.beta", "-1.0.0", "1.0.0 "]:
            self.assertIsNone(version_key(version), version)


class TestResolve(unittest.TestCase):
    def test_major(self):
        versions = catalog("1.9.4", "1.12.5", "1.13.0", "2.0.1", prerelease=["1.14.0-rc1"])
        self.assertEqual(resolve("1", versions), "1.13")
        self.assertEqual(resolve("2", versions), "2.0")

    def test_major_ignores_prereleases(self):
        versions = catalog("1.12.5", prerelease=["1.13.0-rc1", "1.13.0-beta1"])
        self.assertEqual(resolve("1", versions), "1.12")

    def test_major_missing(self):
        with self.assertRaises(ResolveError):
            resolve("3", catalog("1.12.5"))

    def test_channels_during_alpha(self):
        versions = catalog("1.12.5", prerelease=["1.13.0-alpha1", "1.13.0-alpha2"])
        self.assertEqual(resolve("alpha", versions), "1.13.0-alpha2")
        self.assertEqual(resolve("beta", versions), "1.12.5")
        self.assertEqual(resolve("rc", versions), "1.12.5")

    def test_channels_during_beta(self):
        versions = catalog("1.12.5", prerelease=["1.13.0-alpha2", "1.13.0-beta1", "1.13.0-beta2"])
        self.assertEqual(resolve("alpha", versions), "1.13.0-beta2")
        self.assertEqual(resolve("beta", versions), "1.13.0-beta2")
        self.assertEqual(resolve("rc", versions), "1.12.5")

    def test_channels_during_rc(self):
        versions = catalog("1.12.5", prerelease=["1.13.0-beta3", "1.13.0-rc2", "1.13.0-rc10"])
        for channel in ["alpha", "beta", "rc"]:
            self.assertEqual(resolve(channel, versions), "1.13.0-rc10")

    def test_channels_after_release(self):
        versions = catalog("1.12.5", "1.13.0", "1.12.6", prerelease=["1.13.0-rc4"])
        for channel in ["alpha", "beta", "rc"]:
            self.assertEqual(resolve(channel, versions), "1.13.0")

    def test_channels_ignore_unsupported_versions(self):
        versions = catalog("1.12.5", prerelease=["1.13.0-DEV", "2.0.0-pre.alpha"])
        self.assertEqual(resolve("alpha", versions), "1.12.5")

    def test_channel_missing(self):
        with self.assertRaises(ResolveError):
            resolve("rc", catalog(prerelease=["1.13.0-beta1"]))

    def test_unsupported_spec(self):
        for spec in ["1.13", "nightly", "-1", "RC", ""]:
            with self.assertRaises(ValueError, msg=spec):
                resolve(spec, catalog("1.12.5"))


class TestMain(unittest.TestCase):
    def run_main(self, *args, versions=None, error=None):
        def download_catalog():
            if error is not None:
                raise error
            return versions
        with mock.patch.object(resolve_version, "download_catalog", download_catalog), \
             mock.patch("sys.stdout") as stdout, mock.patch("sys.stderr"):
            status = resolve_version.main(["resolve_version.py", *args])
        printed = "".join(call.args[0] for call in stdout.write.call_args_list)
        return status, printed.strip()

    def test_success(self):
        versions = catalog("1.12.5", prerelease=["1.13.0-rc1"])
        self.assertEqual(self.run_main("1", versions=versions), (0, "1.12"))
        self.assertEqual(self.run_main("rc", versions=versions), (0, "1.13.0-rc1"))

    def test_usage_errors(self):
        for args in [(), ("1", "2"), ("1.13",), ("-1",), ("nightly",)]:
            self.assertEqual(self.run_main(*args)[0], 2, args)

    def test_download_errors(self):
        for error in [OSError("offline"), ValueError("bad json")]:
            self.assertEqual(self.run_main("1", error=error), (1, ""))

    def test_resolve_errors(self):
        self.assertEqual(self.run_main("3", versions=catalog("1.12.5")), (1, ""))


if __name__ == "__main__":
    unittest.main()
