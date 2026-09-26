# Osaka City (大阪市)

Support for schedules provided by [Osaka City (大阪市)](https://www.city.osaka.lg.jp/kankyo/page/0000370521.html).

Source for household waste collection weekdays in Osaka City, Japan.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: city_osaka_lg_jp
      args:
        ward: WARD
        address: ADDRESS
        area: AREA
```

### Configuration Variables

**ward**  
*(string) (required)*

**address**  
*(string) (required)*

**area**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: city_osaka_lg_jp
      args:
        ward: abeno
        address: "\u677E\u866B\u901A3\u4E01\u76EE5\u756A"
        area: "\u4E0A\u8A18\u4EE5\u5916"
```

## How to get the source arguments

Pick your ward, then enter your address in any of the usual forms: '浮田1丁目2番', '浮田1丁目2番地5号', '浮田1-2-5' or the full '大阪市北区浮田一丁目2-5' (the 号 is not needed). Towns listed without a chome take the ban directly ('味原町1番'). A town name alone lists its blocks. Check the spelling on the text version of the city's map: https://www.city.osaka.lg.jp/contents/wdu150/trashmap/text/index.html . A few blocks are split into areas with different weekdays (a 号 range, a building, '軽四輪車(小さい車)で収集している地域' or '上記以外'); only then fill in the block detail, from the values offered. Only the weekly schedule is published, so year-end and New Year breaks are not reflected.
