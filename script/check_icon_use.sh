#!/usr/bin/env sh

declare -a excl_arr=(
    "abfall_havelland_de.py"
    "abfall_lippe_de.py"
    "abfall_lro_de.py"
    "abfallkalender_gifhorn_de.py"
    "abfallwirtschaft_fuerth_eu.py"
    "abfallwirtschaft_pforzheim_de.py"
    "abfallwirtschaft_vechta_de.py"
    "abfuhrplan_landkreis_neumarkt_de.py"
)

for full_file in $(git grep --name "mdi:" custom_components/waste_collection_schedule/waste_collection_schedule/source/)
do
    # echo $full_file
    filename=$(basename $full_file)
    # echo $filename
    skip=false
    for exclude in "${excl_arr[@]}"
    do
        if [ "$exclude" == "$filename" ]
        then
            echo Skipping $filename
            skip=true
        fi
    done
    if [ "$skip" = "false" ]
    then
        echo "File $filename has locally declared icons"
    fi
done

## This is the expected
git grep -q "mdi:" custom_components/waste_collection_schedule/waste_collection_schedule/source/
if [ $? -eq "0" ]; then
    # echo "Exit code == 0 -> match found -> make exit 1"
    exit 1
fi
# echo "Exit code != 0 -> no match found -> make zero exit"
exit 0