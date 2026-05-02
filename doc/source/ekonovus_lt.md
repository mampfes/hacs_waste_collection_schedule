# Ekonovus

Support for schedules provided by [UAB "Ekonovus"](https://www.ekonovus.lt), a waste collection company operating in Lithuania.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ekonovus_lt
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Part of the address as shown in the public Ekonovus schedule (e.g. `Margirio g. 16`). Must be unique enough to match a single property.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ekonovus_lt
      args:
        address: Margirio g. 16
```

## How to get the source argument

Visit the [Ekonovus schedule page](https://www.ekonovus.lt/grafikai/) and find your address in the public report. Use the same address string (or a uniquely matching prefix) as the `address` argument.
