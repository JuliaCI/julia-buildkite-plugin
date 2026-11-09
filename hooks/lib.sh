# shellcheck shell=bash
# Helpers shared by the hooks, kept in a separate file so that they can be tested
# without running a hook. Sourced; must not change shell options or traps.

is_windows() { [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; }

# The directory this plugin may write to. In order of precedence:
#
# 1. the `cache_dir` option (`BUILDKITE_PLUGIN_JULIA_CACHE_DIR`), used as is;
# 2. `$XDG_CACHE_HOME/julia-buildkite-plugin`, where the runner points
#    `XDG_CACHE_HOME` at the cache it provides for the job;
# 3. `$HOME/.cache/julia-buildkite-plugin`.
#
# Per the XDG base directory spec, a relative `XDG_CACHE_HOME` is invalid and ignored.
jbp_cache_dir() {
    if [[ -n "${BUILDKITE_PLUGIN_JULIA_CACHE_DIR:-}" ]]; then
        printf '%s\n' "${BUILDKITE_PLUGIN_JULIA_CACHE_DIR}"
        return
    fi
    local xdg="${XDG_CACHE_HOME:-}"
    if [[ "${xdg}" == /* || "${xdg}" =~ ^[A-Za-z]:[\\/] ]]; then
        printf '%s\n' "${xdg%/}/julia-buildkite-plugin"
    else
        printf '%s\n' "${HOME}/.cache/julia-buildkite-plugin"
    fi
}

# Compose `JULIA_DEPOT_PATH` from the plugin's writable depot and an inherited value:
#
#     jbp_depot_path SEP OWN INHERITED [ALIAS...]
#
# The writable depot goes first, so that Pkg and Julia write there, and the inherited
# entries follow in their original order, so that read-only depots provided by the
# runner (e.g. an artifact store) are searched before anything is downloaded. Entries
# equal to OWN or one of its ALIASes are dropped, as happens when the plugin runs twice
# in one job, and so are repeated empty entries. The result always contains an empty
# entry, which Julia expands to the depots bundled with the Julia installation (and their
# stdlib package images); if the inherited value has none, one is appended.
jbp_depot_path() {
    local sep="$1" own="$2" inherited="$3"
    shift 3

    local result="${own}" has_empty=false
    if [[ -n "${inherited}" ]]; then
        local rest="${inherited}${sep}" entry alias duplicate
        while [[ -n "${rest}" ]]; do
            entry="${rest%%"${sep}"*}"
            rest="${rest#*"${sep}"}"
            duplicate=false
            for alias in "${own}" "$@"; do
                if [[ -n "${entry}" && "${entry%[/\\]}" == "${alias%[/\\]}" ]]; then
                    duplicate=true
                fi
            done
            if [[ -z "${entry}" ]]; then
                ${has_empty} && duplicate=true
                has_empty=true
            fi
            ${duplicate} && continue
            result="${result}${sep}${entry}"
        done
    fi
    ${has_empty} || result="${result}${sep}"
    printf '%s\n' "${result}"
}
