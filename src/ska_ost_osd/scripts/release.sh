#!/bin/bash

base_path=$(dirname "$(readlink -f "release.sh")")

observatory_file_location="$base_path/tmdata/observatory_policies.json"
version_mapping_file_location="$base_path/tmdata/version_mapping/cycle_gitlab_release_version_mapping.json"
latest_release_file_location="$base_path/tmdata/version_mapping/latest_release.txt"

function CheckFileExists (){

    if [ -f $1 ]; then
        return 0
    else
        echo $1 "Doesn't Exists"
        return 1
    fi

}

function GetCycleId ()
{
    cycle_id=$(jq -r --arg file_location "$observatory_file_location" '.cycle_number' $observatory_file_location)
    new_cycle_id="cycle_${cycle_id}"
}


function UpdateAndAddValue ()
{
    jq --arg new_cycle_id "$new_cycle_id" --arg version "$1" '
        if has($new_cycle_id) then
            .[$new_cycle_id] += [$version] |
            .[$new_cycle_id] = (.[$new_cycle_id] | unique)
        else
            .[$new_cycle_id] = [$version]
        end
    ' "$version_mapping_file_location" > tmp.json && mv tmp.json "$version_mapping_file_location"
}

function UpdateLatestRelease ()
{
    echo "$1" > "$latest_release_file_location"
}

CheckFileExists $observatory_file_location

if [ $? -eq 0 ]; then
    GetCycleId
fi

CheckFileExists $version_mapping_file_location

if [ $? -eq 0 ]; then
    UpdateAndAddValue $1
fi

CheckFileExists $latest_release_file_location

if [ $? -eq 0 ]; then
    UpdateLatestRelease $1
fi
