# Neu-Ulm

Support for schedules provided by [nu-neu-ulm.de](https://nu.neu-ulm.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: neu_ulm_de
      args:
        region: BEZIRK
```

### Configuration Variables

**region**  
_(string) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: neu_ulm_de
      args:
        region: "Bezirk 1"
```

## How to get the source arguments

Visit the [Neu-Ulm.de](https://nu.neu-ulm.de/buerger-service/leben-in-neu-ulm/abfall-sauberkeit/abfallkalender) page and lookup the correct "Bezirk".
