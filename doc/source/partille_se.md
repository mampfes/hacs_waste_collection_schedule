# Partille kommun

Support for waste collection schedules provided by [Partille kommun](https://vatjanst.partille.se/FutureWeb/SimpleWastePickup/SimpleWastePickup), serving the municipality of Partille, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: partille_se
      args:
        street_address: STREET_ADDRESS
