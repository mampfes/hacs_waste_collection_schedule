# Neu-Ulm

Support for schedules provided by [Neu-Ulm](https://nu.neu-ulm.de/buerger-service/leben-in-neu-ulm/abfall-sauberkeit/abfallkalender).

Source for Neu-Ulm.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: neu_ulm_de
      args:
        region: REGION
```

### Configuration Variables

**region**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: neu_ulm_de
      args:
        region: Bezirk 1
```
