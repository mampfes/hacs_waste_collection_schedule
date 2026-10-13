# Värmdö Sophämtning

Support for schedules provided by [Värmdö Sophämtning](https://www.varmdo.se).

Source for Värmdö household waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: varmdo_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: varmdo_se
      args:
        street_address: "Rosenmalmsv\xE4gen"
```

## How to get the source arguments

Enter your street address as shown in the Värmdö kommun address search, ideally with the house number.
