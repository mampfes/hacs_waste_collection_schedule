# KAEV Niederlausitz

Support for schedules provided by [KAEV Niederlausitz](https://www.kaev.de/).

Source for Kommunaler Abfallverband Niederlausitz waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kaev_niederlausitz
      args:
        abf_suche: ABF_SUCHE
```

### Configuration Variables

**abf_suche**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kaev_niederlausitz
      args:
        abf_suche: Luckau / OT Zieckau
```
