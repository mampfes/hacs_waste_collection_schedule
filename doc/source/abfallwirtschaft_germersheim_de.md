# Abfallwirtschaft Germersheim

Support for schedules provided by [Abfallwirtschaft Germersheim](https://www.abfallwirtschaft-germersheim.de).

Source für Abfallkalender Kreis Germersheim

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_germersheim_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_germersheim_de
      args:
        city: Bellheim
        street: Albert-Schweitzer-Str.
```
