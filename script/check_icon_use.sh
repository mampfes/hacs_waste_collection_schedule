#!/usr/bin/env sh

git grep -q "mdi:" custom_components/waste_collection_schedule/waste_collection_schedule/source/
if [ $? -eq "0" ]; then
    # echo "Exit code == 0 -> match found -> make exit 1"
    exit 1
fi
# echo "Exit code != 0 -> no match found -> make zero exit"
exit 0