# AWBKoeln.de

Add support for schedules provided by `AWBKoeln.de`.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awbkoeln_de
      args:
        street_code: STREET_CODE
        building_number: BUILDING_NUMBER
```

### Configuration Variables

**street_code**<br>
*(string) (required)*

**building_number**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awbkoeln_de
      args:
        street_code: 4272
        building_number: 10
```

## How to get the source arguments

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/package/wizard/awbkoeln_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/package/wizard/awbkoeln_de.py).

Just run this script from a shell and answer the questions.
