# Stadtreinigung Hamburg

Add support for schedules provided by [stadtreinigung.hamburg](https://www.stadtreinigung.hamburg/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_hamburg
      args:
        asId: ASID
        hnId: HNID
```

### Configuration Variables

**asId**<br>
*(string) (required)*

**hnId**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_hamburg
      args:
        asId: 5087
        hnId: 113084
```

## How to get the source arguments

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/stadtreinigung_hamburg.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/stadtreinigung_hamburg.py).

Just run this script from a shell and answer the questions.
