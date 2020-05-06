# Jumomind.de

Support for schedules provided by [jumomind.de](https://jumomind.de/). Jumomind is a service from [junker.digital](https://junker.digital/).

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

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/package/wizard/jumomind_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/package/wizard/jumomind_de.py).

Just run this script from a shell and answer the questions.
