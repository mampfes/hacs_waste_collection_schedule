#!/bin/bash

fixpath="custom_components/waste_collection_schedule/waste_collection_schedule/source/"

for file in $(git grep --name mdi: -- "$fixpath"); do
    echo Trying to fix file $file
    sed -i -e 's/"mdi:biohazard"/Icons.ICON_BIOHAZARD/g' $file
    sed -i -e 's/"mdi:bottle-wine-outline"/Icons.ICON_CLEAR_GLASS/g' $file
    sed -i -e 's/"mdi:bottle-wine"/Icons.ICON_COLORED_GLASS/g' $file
    sed -i -e 's/"mdi:food"/Icons.ICON_COMPOST/g' $file
    sed -i -e 's/"mdi:desktop-classic"/Icons.ICON_ELECTRONICS/g' $file
    sed -i -e 's/"mdi:leaf"/Icons.ICON_GARDEN_WASTE/g' $file
    sed -i -e 's/"mdi:trash-can"/Icons.ICON_GENERAL_TRASH/g' $file
    sed -i -e 's/"mdi:delete-empty"/Icons.ICON_LANDFILL/g' $file
    sed -i -e 's/"mdi:nail"/Icons.ICON_METAL/g' $file
    sed -i -e 's/"mdi:newspaper"/Icons.ICON_NEWSPAPER/g' $file
    sed -i -e 's/"mdi:package-variant"/Icons.ICON_GENERAL_TRASH/g' $file
    sed -i -e 's/"mdi:bottle-soda-classic-outline"/Icons.ICON_PLASTIC/g' $file
    sed -i -e 's/"mdi:recycle"/Icons.ICON_RECYCLE/g' $file
done

echo ""
echo "Now manually tidy up the things the script could not fix:"
echo "1. Run \"git status\" to find which filed have been modified"
echo "2. If the file does not contian the following import, add it \"from const import Icons\""
echo "3. Run \"git grep mdi: -- custom_components/waste_collection_schedule/waste_collection_schedule/source/\" to see if there are any remaining icons that can be manually fixed"
echo "4. Run \"./script/check_icon_use.sh\" to see what files should be removed from whitelist in that script"
