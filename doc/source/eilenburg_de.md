# Eilenburg

Support for schedules provided by [Eilenburg](https://www.eilenburg.de).

Source for waste collection in Eilenburg (Saxony, Germany).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eilenburg_de
      args:
        areas: AREAS
```

### Configuration Variables

**areas**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eilenburg_de
      args:
        areas:
        - EB Berg
        - EB 1
```

## How to get the source arguments

List of collection areas, e.g. ['EB Berg', 'EB 1']. Residual/paper areas: EB Berg, EB Stadt, EB Ost, EB Ortsteile Dörfer. Yellow-bag areas: EB 1 to EB 5.
