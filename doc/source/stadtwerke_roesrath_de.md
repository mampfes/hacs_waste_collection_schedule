# Stadtwerke Rösrath

Support for schedules provided by [Stadtwerke Rösrath](https://www.stadtwerke-roesrath.de/service/abfuhrkalender/).

Source for 'Stadtwerke Rösrath'.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtwerke_roesrath_de
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
    - name: stadtwerke_roesrath_de
      args:
        street: Ahornweg
```
