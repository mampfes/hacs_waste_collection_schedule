# AWB Köln

Support for schedules provided by [AWB Köln](https://www.awbkoeln.de).

Source for Abfallwirtschaftsbetriebe Köln waste collection.

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

**street_code**  
*(string) (required)*

**building_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awbkoeln_de
      args:
        street_code: 2
        building_number: 50
```
