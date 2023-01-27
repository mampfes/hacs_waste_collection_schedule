# Jönköping - June Avfall & Miljö

Support for schedules provided by [June Avfall & Miljö](https://minasidor.juneavfall.se/FutureWebJuneBasic/SimpleWastePickup/SimpleWastePickup), serving the municipality of Jönköping, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: juneavfall_se
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
    - name: juneavfall_se
      args:
        street_address: Smedjegatan 20, Jönköping
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://minasidor.juneavfall.se/FutureWebJuneBasic/SimpleWastePickup/SimpleWastePickup).
