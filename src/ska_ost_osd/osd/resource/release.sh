#!/bin/bash

base_path=$(dirname "$(readlink -f "release.sh")")

observatory_file_location="$base_path/tmdata/osd_data/observatory_policies.json"
version_mapping_file_location="$base_path/src/ska_telmodel/osd/version_mapping/cycle_gitlab_release_version_mapping.json"

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
    key_exists=$(jq --arg new_cycle_id "$new_cycle_id" --arg version "$1" --arg file_location "$version_mapping_file_location" 'select(has($new_cycle_id))[$new_cycle_id] = [$version]' $version_mapping_file_location > tmp.json && mv tmp.json $version_mapping_file_location)
    key_not_exists=$(jq --arg new_cycle_id "$new_cycle_id" --arg version "$1" --arg file_location "$version_mapping_file_location" '[.] | map(. + {($new_cycle_id): [$version]}) | .[0]' $version_mapping_file_location  > tmp.json && mv tmp.json $version_mapping_file_location)
}

CheckFileExists $observatory_file_location

if [ $? -eq 0 ]; then
    GetCycleId
fi

CheckFileExists $version_mapping_file_location

if [ $? -eq 0 ]; then
    UpdateAndAddValue $1
fi
