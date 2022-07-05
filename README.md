# julia-buildkite-plugin

This plugin provides a convenient way to download and install [Julia](https://julialang.org/) for use in other plugins or commands.

## Example

```yaml
steps:
  - label: ":julia: Run tests on 1.6"
    plugins:
      - JuliaCI/julia#v1:
          version: 1.6
      - JuliaCI/julia-test#v1:
```

## Options

* `version`: A version to download and use, examples are `1`, `1.6`, `1.5.3`, `1.7-nightly`.
* `isolated_depot`: a boolean which defaults to `true`, automatically configuring Julia to use a pipeline-specific depot. If `false`, the default depot (usually `$HOME/.julia`) is used.
* `persist_depot_dirs`: a string of comma-separated directories to persist from pipeline run to pipeline run within the isolated depot. Cannot be set if `isolated_depot` is `false`. Defaults to `"packages,artifacts,compiled,logs,datadeps,scratchspaces"`.

### Advanced Options

* `arch`: a string specifying the architecture to download Julia for. Defaults to `uname -m`.
* `cache_dir`: a string specifying a location for maintaining a cache of Julia installations, depots, etc. Defaults to `${HOME}/.cache/julia-buildkite-plugin`. Persist this directory on your agents to speed up subsequent builds.
* `cleanup_collect_delay`: a string specifying a period in seconds after which package garbage collection, i.e. [`Pkg.gc`](https://pkgdocs.julialang.org/v1/api/#Pkg.gc), will consider orphaned items for cleanup. Defaults to `604800` seconds, i.e. 1 week.
* `debug_plugin`: a boolean, which defaults to `false`, severely increasing the verbosity of the plugin for debugging purposes.
* `python`: a string specifying the path to a Python 3 distribution. The plugin will try to autodetect the location of a Python 3 installation by default.
* `update_registry`: a boolean, which defaults to `true`, indicating whether to update the package registry.
