# Gemeinde Seuzach

Support for schedules provided by [Gemeinde Seuzach](https://www.seuzach.ch).

Source for waste collection services in Seuzach, Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: seuzach_ch
```

### Configuration Variables

No configuration arguments are required.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: seuzach_ch
```

## How to get the source arguments

Seuzach publishes a single municipality-wide collection calendar, so no address or other argument is required.
