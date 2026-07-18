# Stadtservice Korneuburg

Support for schedules provided by [Stadtservice Korneuburg](https://www.korneuburg.gv.at).

Source for Stadtservice Korneuburg, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: korneuburg_stadtservice_at
      args:
        street_name: STREET_NAME
        street_number: STREET_NUMBER
        teilgebiet: TEILGEBIET
```

### Configuration Variables

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

**teilgebiet**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: korneuburg_stadtservice_at
      args:
        street_name: Hauptplatz
        street_number: 39
```
