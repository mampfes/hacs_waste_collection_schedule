# VIVAB Sophämtning

Support for schedules provided by [VIVAB Sophämtning](https://www.vivab.se).

Source for VIVAB waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vivab_se
      args:
        street_address: STREET_ADDRESS
        building_id: BUILDING_ID
```

### Configuration Variables

**street_address**  
*(string) (required)*

**building_id**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vivab_se
      args:
        street_address: "V\xE4stra Vallgatan 2, Varberg"
```

## How to get the source arguments

Enter your street address ending in its locality (e.g. 'Östergränd 4, Falkenberg'). Where several buildings share the address, give 'building_id' (the number in brackets in the provider's search) and just 'Varberg' or 'Falkenberg' as the address.
