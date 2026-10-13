# Norrtälje Vatten & Avfall

Support for schedules provided by [Norrtälje Vatten & Avfall](https://sjalvservice.nvaa.se/).

Source for Norrtälje Vatten & Avfall waste collection services, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nvaa_se
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
    - name: nvaa_se
      args:
        street_address: "Hamndalsv\xE4gen 2, Norrt\xE4lje"
```

## How to get the source arguments

Enter the address as the self-service site writes it, street and number followed by the locality, e.g. `Hamndalsvägen 2, Norrtälje`.
