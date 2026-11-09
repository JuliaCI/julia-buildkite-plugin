import os
import subprocess
import unittest

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "lib.sh")


def bash(script, env):
    """Run `script` with hooks/lib.sh sourced, in a clean environment plus `env`."""
    base = {"PATH": os.environ["PATH"], "HOME": "/home/user", "OSTYPE": "linux-gnu"}
    base.update(env)
    out = subprocess.run(["bash", "-c", 'set -euo pipefail; source "$0"; ' + script, LIB],
                         env=base, check=True, capture_output=True, text=True)
    return out.stdout.rstrip("\n")


def cache_dir(**env):
    return bash("jbp_cache_dir", env)


def depot_path(sep, own, inherited, *aliases):
    out = subprocess.run(["bash", "-c", 'set -euo pipefail; source "$0"; jbp_depot_path "$@"',
                          LIB, sep, own, inherited, *aliases],
                         check=True, capture_output=True, text=True)
    return out.stdout.rstrip("\n")


class TestCacheDir(unittest.TestCase):
    def test_default(self):
        self.assertEqual(cache_dir(), "/home/user/.cache/julia-buildkite-plugin")

    def test_xdg(self):
        self.assertEqual(cache_dir(XDG_CACHE_HOME="/cache"), "/cache/julia-buildkite-plugin")
        self.assertEqual(cache_dir(XDG_CACHE_HOME="/cache/"), "/cache/julia-buildkite-plugin")

    def test_xdg_windows(self):
        self.assertEqual(cache_dir(XDG_CACHE_HOME="C:\\cache"),
                         "C:\\cache/julia-buildkite-plugin")
        self.assertEqual(cache_dir(XDG_CACHE_HOME="D:/cache"), "D:/cache/julia-buildkite-plugin")

    def test_xdg_invalid(self):
        # Empty and relative values are ignored, as the XDG spec requires.
        for value in ["", "cache", "./cache", "~/cache"]:
            self.assertEqual(cache_dir(XDG_CACHE_HOME=value),
                             "/home/user/.cache/julia-buildkite-plugin", value)

    def test_explicit_option_wins(self):
        self.assertEqual(cache_dir(BUILDKITE_PLUGIN_JULIA_CACHE_DIR="/opt/jbp",
                                   XDG_CACHE_HOME="/cache"), "/opt/jbp")
        # An empty option counts as unset.
        self.assertEqual(cache_dir(BUILDKITE_PLUGIN_JULIA_CACHE_DIR="",
                                   XDG_CACHE_HOME="/cache"), "/cache/julia-buildkite-plugin")


class TestDepotPath(unittest.TestCase):
    def test_nothing_inherited(self):
        # The trailing empty entry adds Julia's bundled depots, as before v1.15.
        self.assertEqual(depot_path(":", "/c/d", ""), "/c/d:")
        self.assertEqual(depot_path(";", "C:\\c\\d", ""), "C:\\c\\d;")

    def test_inherited_store(self):
        self.assertEqual(depot_path(":", "/c/d", "/store"), "/c/d:/store:")
        self.assertEqual(depot_path(":", "/c/d", "/store:"), "/c/d:/store:")
        self.assertEqual(depot_path(":", "/c/d", "/s1:/s2"), "/c/d:/s1:/s2:")

    def test_inherited_order_and_empty_entries_kept(self):
        self.assertEqual(depot_path(":", "/c/d", ":/store"), "/c/d::/store")
        self.assertEqual(depot_path(":", "/c/d", "/s1::/s2"), "/c/d:/s1::/s2")
        self.assertEqual(depot_path(":", "/c/d", ":"), "/c/d:")

    def test_inherited_own_depot(self):
        # e.g. when the plugin runs twice in one job
        self.assertEqual(depot_path(":", "/c/d", "/c/d:"), "/c/d:")
        self.assertEqual(depot_path(":", "/c/d", "/c/d/:/store"), "/c/d:/store:")
        self.assertEqual(depot_path(":", "/c/d", "/store:/c/d:"), "/c/d:/store:")

    def test_windows(self):
        own = "C:\\cache\\julia-buildkite-plugin\\depots\\p"
        msys = "/c/cache/julia-buildkite-plugin/depots/p"
        self.assertEqual(depot_path(";", own, "D:\\store", msys), own + ";D:\\store;")
        self.assertEqual(depot_path(";", own, own + ";", msys), own + ";")
        self.assertEqual(depot_path(";", own, msys + ";D:\\store", msys), own + ";D:\\store;")

    def test_spaces(self):
        self.assertEqual(depot_path(":", "/a b/d", "/my store"), "/a b/d:/my store:")


if __name__ == "__main__":
    unittest.main()
