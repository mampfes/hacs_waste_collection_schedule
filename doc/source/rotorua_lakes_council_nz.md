# Rotorua Lakes Council

Support for schedules provided by [Rotorua Lakes Council](https://www.rotorualakescouncil.nz).

Source for Rotorua Lakes Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rotorua_lakes_council_nz
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
    - name: rotorua_lakes_council_nz
      args:
        address: 1061 Haupapa Street
```

## How to get the source arguments

Enter your street address, e.g. '1061 Haupapa Street'.
