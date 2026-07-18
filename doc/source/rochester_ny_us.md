# Rochester, NY

Support for schedules provided by [Rochester, NY](https://www.cityofrochester.gov).

Source for Rochester, NY waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rochester_ny_us
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rochester_ny_us
      args:
        address: 124 Parsells Ave, Rochester, NY
```

## How to get the source arguments

Enter your street address within the City of Rochester (e.g. '124 Parsells Ave, Rochester, NY').
