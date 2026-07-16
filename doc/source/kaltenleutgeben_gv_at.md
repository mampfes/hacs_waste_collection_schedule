# Marktgemeinde Kaltenleutgeben

Support for waste collection schedules provided by [Marktgemeinde Kaltenleutgeben](https://www.kaltenleutgeben.gv.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kaltenleutgeben_gv_at
      args: {}
```

The Kaltenleutgeben waste calendar is a single town-wide schedule, so no arguments are required.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kaltenleutgeben_gv_at
      args: {}
```

## How to get the source arguments

No arguments are needed. The source reads the current schedule from <https://www.kaltenleutgeben.gv.at/Muellkalender_NEU>.
