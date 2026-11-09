# julia-buildkite-plugin

This plugin provides a convenient way to download and install [Julia](https://julialang.org/) for use in other plugins or commands.

## Example

```yaml
steps:
  - label: ":julia: Run tests on 1.6"
    plugins:
      - JuliaCI/julia#v2:
          version: 1.6
      - JuliaCI/julia-test#v1:
```

## Options

* `version`: A version to download and use, examples are `1`, `1.6`, `1.5.3`,
  `1.13.0-beta3`, `nightly`, `1.7-nightly`, `rc`, `beta` and `alpha`. The
  latter three follow juliaup's channels of the same name: `rc` selects the
  newest release or release candidate, `beta` also considers betas, and `alpha`
  also considers alphas.
* `isolated_depot`: a boolean which defaults to `true`, automatically
  configuring Julia to use a pipeline-specific depot. If `false`, the default
  depot (usually `$HOME/.julia`) is used.
* `persist_depot_dirs`: a string of comma-separated directories to persist from
  pipeline run to pipeline run within the isolated depot. Cannot be set if
  `isolated_depot` is `false`. Defaults to
  `"packages,artifacts,compiled,logs,datadeps,scratchspaces"`.

### Advanced Options

* `arch`: a string specifying the architecture to download Julia for. Defaults
  to `uname -m`.
* `cache_dir`: a string specifying the directory the plugin keeps Julia
  installations, downloads and depots in. Overrides the default described in
  [Cache directory](#cache-directory).
* `debug_plugin`: a boolean, which defaults to `false`, severely increasing the
  verbosity of the plugin for debugging purposes.
* `python`: a string specifying the path to a Python 3 distribution. The plugin
  will try to autodetect the location of a Python 3 installation by default.
* `update_registry`: a boolean, which defaults to `true`, indicating whether to
  update the package registry.

The options `compiled_size_limit`, `artifacts_size_limit`, `depot_size_limit`,
`depot_age_limit` and `pipeline_age_limit` were removed in v2. They are still
accepted, but only produce a warning.

## Cache directory

The plugin keeps everything it downloads or creates in one directory:

1. the `cache_dir` option, if set (also when it comes from the
   `BUILDKITE_PLUGIN_JULIA_CACHE_DIR` environment variable);
2. otherwise `$XDG_CACHE_HOME/julia-buildkite-plugin`, if `XDG_CACHE_HOME` is
   set to an absolute path;
3. otherwise `$HOME/.cache/julia-buildkite-plugin`.

Inside it, `downloads/` holds the Julia archives, `julia_installs/` the unpacked
installations, `depots/<pipeline id>/` the isolated depots, and `tmp/` work in
progress. Keep the directory between jobs to make them much faster.

### The contract with the runner

Whatever starts the Buildkite agent (a job scheduler, agent hooks, or a person
on a laptop) is the *runner*. The plugin and the runner split the work as
follows:

* **The runner provides the cache.** It points `XDG_CACHE_HOME` at a writable
  directory for the job, and chooses which jobs share it (e.g. per agent slot,
  pipeline and trust level). Other tools that follow the XDG convention end up
  in the same place.
* **The plugin writes only to its own subdirectory**,
  `<cache>/julia-buildkite-plugin/`, and never limits its size: it does not
  measure it, trim artifacts or compilation caches, or remove old depots.
* **The runner owns eviction.** It deletes caches as a whole when it needs
  space or when they get too old. The plugin tolerates its directory
  disappearing between jobs, and other jobs using it at the same time:
  downloads and unpacks happen in `tmp/` and are renamed into place when
  complete, and an incomplete or outdated installation is detected and
  replaced. The plugin removes only its own leftovers from `tmp/`.
* **Read-only stores are found through `JULIA_DEPOT_PATH`.** When the depot is
  isolated, the plugin sets `JULIA_DEPOT_PATH` to its own depot followed by the
  value it inherited, e.g. `/cache/julia-buildkite-plugin/depots/<id>:/store:`.
  Julia and Pkg write to the first depot only, and find artifacts, packages and
  compilation caches in the later ones, so a runner can offer a shared,
  read-only artifact store by setting `JULIA_DEPOT_PATH=/store`. The result
  always contains an empty entry (added at the end if the inherited value has
  none), which Julia expands to the depots bundled with its installation.
  Without an inherited value this is `<depot>:`, as before v2. On Windows the
  separator is `;`.

A runner that does not evict caches, such as an agent with a persistent
`$HOME`, must clean the cache directory itself, e.g. with a cron job that
removes it when the disk fills up, or stay on v1 of this plugin, which prunes
its depots after every job.

## Migrating from v1 to v2

v2 removes all size management from the plugin. Before moving a pipeline to
`JuliaCI/julia#v2`, make sure the agents it runs on have a runner that evicts
the cache directory (see above); otherwise the directory grows without bound.

* The pre-exit hook no longer runs `du` on the depot, trims the `compiled` and
  `artifacts` directories, wipes depots that are too large, or removes depots
  of pipelines that have not run for 30 days. Their options are ignored with a
  warning.
* The cache directory now honours `XDG_CACHE_HOME`. An explicit `cache_dir`
  (or `BUILDKITE_PLUGIN_JULIA_CACHE_DIR`) still takes precedence, so runners
  that set it keep working; new runners should set `XDG_CACHE_HOME` instead.
* An inherited `JULIA_DEPOT_PATH` is now kept after the isolated depot instead
  of being replaced. If your agents export a `JULIA_DEPOT_PATH` that jobs
  should not see, unset it in the agent environment.
* On Windows, `JULIA_DEPOT_PATH` now contains a Windows path (`C:\...`).
* Installations are now marked complete; the first v2 job unpacks each cached
  Julia version once more.
