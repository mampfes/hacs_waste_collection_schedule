# Gemeinde Maur

Support for schedules provided by [Gemeinde Maur](https://www.maur.ch/themen/bauen-umwelt/abfall-recycling/termine.html).

Source for waste collection in Maur, Canton of Zurich, Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: maur_ch
```

### Configuration Variables

No configuration arguments are required.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: maur_ch
```

## How to get the source arguments

Maur publishes a single municipality-wide collection calendar, so no address or other argument is required.
