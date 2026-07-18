# Abfallwirtschaft Südholstein

Support for schedules provided by [Abfallwirtschaft Südholstein](https://www.awsh.de).

Source for Abfallwirtschaft Südholstein

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awsh_de
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
    - name: awsh_de
      args:
        city: Reinbek
        street: Ahornweg
```
