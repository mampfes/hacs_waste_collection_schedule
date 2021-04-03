# Abfallwirtschaft Stuttgart

Support for schedules provided by [stuttgart.de](https://service.stuttgart.de/lhs-services/aws/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stuttgart_de
      args:
        street: ORT_SEL
        streetnr: STR_SEL
```

### Configuration Variables

**street**<br>
*(string) (required)*

**streetnr**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stuttgart_de
      args:
        street: Im Steinengarten
        streetnr: 7
```

## How to get the source arguments

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/stuttgart_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/stuttgart_de.py).

Just run this script from a shell and answer the questions.
