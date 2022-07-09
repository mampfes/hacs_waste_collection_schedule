# SSAM

TODO!

Support for schedules provided by [Lerum Vatten och Avlopp](https://vatjanst.lerum.se/FutureWeb/SimpleWastePickup/SimpleWastePickup), serving the municipality of Lerum, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lerum_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lerum_se
      args:
        street_address: Götebordsvägen 16, Lerum
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://vatjanst.lerum.se/FutureWeb/SimpleWastePickup/SimpleWastePickup).
