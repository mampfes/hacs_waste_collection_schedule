# Jumomind.de

Add support for schedules provided by `Jumomind.de`.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: SERVICE_ID
        city_id: CITY_ID
        area_id: AREA_ID
```

### Configuration Variables

**service_id**<br>
*(string) (required)*

**city_id**<br>
*(string) (required)*

**area_id**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: zaw
        city_id: 106
        area_id: 94
```

## How to get the source arguments

Please see the very good description on https://github.com/tuxuser/abfallapi_jumomind_ha.
