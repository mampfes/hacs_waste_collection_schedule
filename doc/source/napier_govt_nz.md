# Napier City Council

Support for schedules provided by [Napier City Council](https://www.napier.govt.nz/).

Source for Napier City Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: napier_govt_nz
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
    - name: napier_govt_nz
      args:
        address: 4 Sheehan Street
```

## How to get the source arguments

Enter your street address as it appears on the [Napier City Council website](https://www.napier.govt.nz/services/properties-and-rates/my-property/), e.g. '4 Sheehan Street'. The address must match a single property.
