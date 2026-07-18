# Abfallwirtschaft Nürnberger Land

Support for schedules provided by [Abfallwirtschaft Nürnberger Land](https://nuernberger-land.de).

Source for Nürnberger Land

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nuernberger_land_de
      args:
        id: ID
```

### Configuration Variables

**id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nuernberger_land_de
      args:
        id: 16952001
```
