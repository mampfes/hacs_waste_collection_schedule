# Northville Township, MI

Support for schedules provided by [Northville Township, MI](https://www.twp.northville.mi.us).

Source for Northville Township, MI waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: northville_township_mi_us
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
    - name: northville_township_mi_us
      args:
        address: 16795 Northville Rd
```

## How to get the source arguments

Enter your street address (e.g. '16795 Northville Rd').
