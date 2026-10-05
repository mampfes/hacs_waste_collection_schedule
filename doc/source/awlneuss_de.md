# AWL Neuss

Support for schedules provided by [AWL Neuss](https://buergerportal.awl-neuss.de/).

Source for Bürgerportal AWL Neuss waste collection.

## Configuration via configuration.yaml

### Using street_name

```yaml
waste_collection_schedule:
  sources:
    - name: awlneuss_de
      args:
        building_number: BUILDING_NUMBER
        street_name: STREET_NAME
```

### Using street_code

```yaml
waste_collection_schedule:
  sources:
    - name: awlneuss_de
      args:
        building_number: BUILDING_NUMBER
        street_code: STREET_CODE
```

### Configuration Variables

**street_name**  
*(string) (alternative)*

**street_code**  
*(string) (alternative)*

**building_number**  
*(string) (required)*

Provide one of: `street_name` or `street_code`.

## Example

### Using street_name

```yaml
waste_collection_schedule:
  sources:
    - name: awlneuss_de
      args:
        building_number: 67
        street_name: Bahnhofstrasse
```

### Using street_code

```yaml
waste_collection_schedule:
  sources:
    - name: awlneuss_de
      args:
        building_number: 13
        street_code: 8650
```

## How to get the source arguments

Enter either the exact street name (street_name) or the street code (street_code), together with the house number (building_number).
