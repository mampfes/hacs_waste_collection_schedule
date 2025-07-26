# Berliner Stadtreinigungsbetriebe

Support for schedules provided by [bsr.de](https://www.bsr.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bsr_de
      args:
        schedule_id: SCHEDID
```

### Configuration Variables

**schedule_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bsr_de
      args:
        schedule_id: "049011000107000039600010"
```

## How to get the source arguments

There is a script with an interactive command line interface which generates the required source configuration:

[custom_components/waste_collection_schedule/waste_collection_schedule/wizard/bsr_de.py](../../custom_components/waste_collection_schedule/waste_collection_schedule/wizard/bsr_de.py).

First, install the Python modules `inquirer` and `requests`.
Then run this script from a shell and answer the questions.
The script will basically ask for the street and the house number.
It will then query the BSR for the `schedule_id`.
