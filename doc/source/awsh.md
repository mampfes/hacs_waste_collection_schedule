# AWSH

Support for schedules provided by [AWSH](https://www.awsh.de)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awsh
      args:
        ortId: Ort ID
        strId: Strassen ID
        waste_types:
          - R..
          - D..
          - B..
```

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awsh
      args:
        ortId: 560
        strId: 860
        waste_types:
          - R02
          - B02
          - D02
          - P04
```

## How to get the source arguments

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/awsh.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/awsh.py).

Just run this script from a shell and answer the questions.