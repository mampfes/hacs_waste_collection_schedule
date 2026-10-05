# Borlänge Energi

Support for schedules provided by [Borlänge Energi](https://www.borlange-energi.se/avfall-och-atervinning/sophamtning).

Waste collection schedule for Borlänge, Sweden

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: borlange_energi_se
      args:
        pickup_address: PICKUP_ADDRESS
```

### Configuration Variables

**pickup_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: borlange_energi_se
      args:
        pickup_address: "Mats Knuts V\xE4g 100"
```

## How to get the source arguments

Enter your pickup address as it appears in the 'När kommer sopbilen?' search on the [Borlänge Energi waste page](https://www.borlange-energi.se/avfall-och-atervinning/sophamtning), e.g. `Mats Knuts Väg 100`.
