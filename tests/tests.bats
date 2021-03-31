#!/usr/bin/env bats

load "$BATS_PATH/load.bash"

# Our scripts require a few of the buildkite environment variables to be set:
export BUILDKITE_PIPELINE_ID="mygreatpipelineid"
export OSTYPE="linux-musl"

@test "Install Julia 1.6" {
    export BUILDKITE_PLUGIN_JULIA_VERSION="1.6"

    run $PWD/hooks/pre-command

    assert_output --partial "New installation detected"
    assert_output --partial "Installation Successful"
    assert_output --partial "Julia Version 1.6"
    assert_success
}

@test "Re-Install Julia 1.6" {
    export BUILDKITE_PLUGIN_JULIA_VERSION="1.6"

    run $PWD/hooks/pre-command

    refute_output --partial "New installation detected"
    assert_output --partial "Installation Successful"
    assert_output --partial "Julia Version 1.6"
    assert_success

    unset BUILDKITE_PLUGIN_JULIA_VERSION
}

@test "Installs Julia 1.5" {
    export BUILDKITE_PLUGIN_JULIA_VERSION="1.5"

    run $PWD/hooks/pre-command

    assert_output --partial "New installation detected"
    assert_output --partial "Installation Successful"
    assert_output --partial "Julia Version 1.5"
    assert_success

    unset BUILDKITE_PLUGIN_JULIA_VERSION
}

@test "Isolated Depot Cleanup" {
    export BUILDKITE_PLUGIN_JULIA_VERSION="1.6"
    export BUILDKITE_PLUGIN_JULIA_ISOLATE_DEPOT="true"
    export BUILDKITE_PLUGIN_JULIA_PERSIST_DEPOT_DIRS="registries,packages"

    run $PWD/hooks/pre-command

    assert_output --partial "Installation Successful"
    assert_output --partial "Julia Version 1.6"
    assert_success

    # Test that if we run the pre-command again, it deletes our `artifacts` directory but not `registries`
    JULIA_DEPOT_PATH=~/.cache/julia-buildkite-plugin/depots/${BUILDKITE_PIPELINE_ID}
    mkdir -p $JULIA_DEPOT_PATH/{artifacts,registries}
    run $PWD/hooks/pre-command

    assert_output --partial "Cleaning out depot at ${JULIA_DEPOT_PATH}"

    [[ ! -d $JULIA_DEPOT_PATH/artifacts ]]
    [[ -d $JULIA_DEPOT_PATH/registries ]]

    unset BUILDKITE_PLUGIN_JULIA_VERSION
    unset BUILDKITE_PLUGIN_JULIA_ISOLATE_DEPOT
    unset BUILDKITE_PLUGIN_JULIA_PERSIST_DEPOT_DIRS
}