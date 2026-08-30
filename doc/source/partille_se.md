# Partille kommun

Support for waste collection schedules provided by [Partille kommun](https://vatjanst.partille.se/FutureWeb/SimpleWastePickup/SimpleWastePickup), serving the municipality of Partille, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: partille_se
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
    - name: partille_se
      args:
        street_address: Tiondevägen 6, Partille
```

## How to get the source argument

The source argument is the address of the property with waste collection. The address can be tested [here](https://vatjanst.partille.se/FutureWeb/SimpleWastePickup/SimpleWastePickup).
