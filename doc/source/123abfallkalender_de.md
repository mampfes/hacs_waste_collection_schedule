# 123abfallkalender

Support for schedules provided by [123abfallkalender](https://www.123abfallkalender.de/).

Source script for 123abfallkalender.de (Ebsdorfergrund)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: 123abfallkalender_de
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: 123abfallkalender_de
      args:
        district: Beltershausen
```

## How to get the source arguments

Select your district from the list.
