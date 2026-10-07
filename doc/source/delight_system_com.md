# ThreeR

Support for schedules provided by [ThreeR](https://threer.delight-system.co.jp/), the garbage collection platform used by many municipalities across Japan (e.g. Shinjuku City, Chiba City).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: delight_system_com
      args:
        municipality: MUNICIPALITY
        area_name: AREA_NAME
        language_code: LANGUAGE_CODE
```

### Configuration Variables

**municipality**
*(string) (required)*

Municipality name in english, lowercase. For example

* `akirunoshi` for あきる野市
* `shinjukuku` for 新宿区

**area_name**
*(string) (required)*

Collection area as shown in the app, e.g. `Aizumi-cho`. Where the app asks for several levels (town and chōme, or ward, chōme, ban and gō), give every level, separated by ` / `, e.g. `Okubo / 1 chome` or `北区 / 浮田1丁目 / 2番 / 2～5号`. The separators may be left out (`Okubo 1 chome`, `浮田1丁目2番2～5号`), and so may the first level (the ward in `浮田1丁目2番2～5号`). A name that occurs more than once in the municipality (such as `1 chome`) is not accepted on its own; the error lists the full paths to choose from.

**language_code**
*(string) (required)*

Language for municipality, area, and waste type labels (`en`, `ja`, or `ko`).

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: delight_system_com
      args:
        municipality: Shinjuku City
        area_name: Aizumi-cho
        language_code: en
```

```yaml
waste_collection_schedule:
  sources:
    - name: delight_system_com
      args:
        municipality: shinjukuku
        area_name: Okubo / 1 chome
        language_code: en
```

```yaml
waste_collection_schedule:
  sources:
    - name: delight_system_com
      args:
        municipality: 大阪市
        area_name: 北区 / 浮田1丁目 / 2番 / 2～5号
        language_code: ja
```

## Setup via the Home Assistant UI

During integration setup, enter your municipality and area name as shown in ThreeR. If a value is not recognised, the form will show matching options fetched from the live API (the same pattern used by other sources such as RSAG in Germany).

If you leave **area name** empty on the first attempt, the setup form will offer a dropdown of the first level of areas for the selected municipality. If the area you pick has further levels, the next attempt offers them, until you reach your collection area.
