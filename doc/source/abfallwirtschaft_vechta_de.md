# AWB Abfallwirtschaft Vechta

Support for schedules provided by [AWB Abfallwirtschaft Vechta](https://www.abfallwirtschaft-vechta.de/).

Source for AWB Abfallwirtschaft Vechta.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_vechta_de
      args:
        stadt: STADT
        strasse: STRASSE
```

### Configuration Variables

**stadt**  
*(string) (required)*

**strasse**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_vechta_de
      args:
        stadt: Vechta
        strasse: An der Hasenweide
```
