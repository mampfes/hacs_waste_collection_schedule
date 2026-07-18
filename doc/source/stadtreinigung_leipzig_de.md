# Stadtreinigung Leipzig

Support for schedules provided by [Stadtreinigung Leipzig](https://stadtreinigung-leipzig.de).

Source for Stadtreinigung Leipzig.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_leipzig_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_leipzig_de
      args:
        street: Bahnhofsallee
        house_number: 7
```
