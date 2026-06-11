# threeR

Support for schedules provided by [threeR](https://threer.delight-system.co.jp/), the garbage collection platform used by many municipalities across Japan (e.g. Shinjuku City, Chiba City).

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

Neighbourhood/chōme name from the app, `Aizumi-cho`.

**language_code**
*(string) (required)*

Language for municipality, area, and waste type labels (`en`, `ja`, or `ko`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: delight_system_com
      args:
        municipality: Shinjuku City
        area_name: Aizumi-cho
        language_code: en
```

## Setup via the Home Assistant UI

During integration setup, enter your municipality and area name as shown in threeR. If a value is not recognised, the form will show matching options fetched from the live API (the same pattern used by other sources such as RSAG in Germany).

If you leave **area name** empty on the first attempt, the setup form will offer a dropdown of all collection areas for the selected municipality.
