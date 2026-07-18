# Gemeinde Muttenz

Support for schedules provided by [Gemeinde Muttenz](https://www.muttenz.ch).

Source for the municipality of Muttenz, Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muttenz_ch
```

### Configuration Variables

No configuration arguments are required.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muttenz_ch
```

## How to get the source arguments

Muttenz publishes a single municipality-wide collection calendar, so no address or other argument is required.
