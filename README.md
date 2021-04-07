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
* `isolated_depot`: a boolean which defaults to `true`, automatically configuring Julia to use a pipeline-specific depot.  If `false`, the default depot (usually `$HOME/.julia`) is used.
* `persist_depot_dirs`: a string of comma-separated directories to persist from pipeline run to pipeline run within the isolated depot.  Cannot be set if `isolated_depot` is `false`.  Defaults to `"registries,packages,artifacts,compiled,datadeps"`.
