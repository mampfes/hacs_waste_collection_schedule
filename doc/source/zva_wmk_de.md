# Abfallwirtschaft Werra-Meißner-Kreis

Support for schedules provided by [Abfallwirtschaft Werra-Meißner-Kreis](https://www.zva-wmk.de/).

Source for Zweckverband Abfallwirtschaft Werra-Meißner-Kreis

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zva_wmk_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zva_wmk_de
      args:
        city: Berkatal - Frankenhain
        street: Teichhof
```
