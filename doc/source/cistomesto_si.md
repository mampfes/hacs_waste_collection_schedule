# Čisto mesto

Support for schedules provided by [Čisto mesto](https://cistomesto.si).

Source for Čisto mesto Ptuj.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cistomesto_si
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
    - name: cistomesto_si
      args:
        region: "Maj\u0161perk"
```
