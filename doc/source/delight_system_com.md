# threeR

Support for schedules provided by [threeR](https://threer1.delight-system.com), the garbage collection app platform used by many municipalities across Japan (e.g. Shinjuku City, Chiba City).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: delight_system_com
      args:
        municipality: MUNICIPALITY
        area_name: AREA_NAME
```

### Configuration Variables

**municipality**  
*(string) (required)*

Municipality name or ID from the threeR app, e.g. `Shinjuku City` or `shinjukuku`.

**area_name**  
*(string) (required)*

Neighbourhood/chōme name from the app, e.g. `Aizumi-cho`.

**language_code**  
*(string) (optional)*

Language for waste type names (`en`, `ja`, or `ko`). Defaults to `en`.

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

During integration setup, enter your municipality and area name as shown in the threeR app. If a value is not recognised, the form will show matching options fetched from the live API (the same pattern used by other sources such as RSAG in Germany).

If you leave **area name** empty on the first attempt, the setup form will offer a dropdown of all collection areas for the selected municipality.
