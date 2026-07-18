# Junker APP

Support for schedules provided by [Junker APP](https://junker.app).

Source for Junker APP.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: junker_app
      args:
        municipality: MUNICIPALITY
        area: AREA
```

### Configuration Variables

**municipality**  
*(string) (required)*

**area**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: junker_app
      args:
        municipality: Boroneddu
```
