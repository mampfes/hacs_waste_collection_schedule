# Schwabach

Support for schedules provided by [Schwabach](https://www.abfuhrplan-schwabach.de/).

Source for the city of Schwabach

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfuhrplan_schwabach_de
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfuhrplan_schwabach_de
      args:
        street: Am Alten Friedhof 3, 3a
```
