# HVCGroep

Support for schedules provided by [stadtreinigung-leipzig.de](https://stadtreinigung-leipzig.de/).

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

**street**<br>
*(string) (required)*

**house_number**<br>
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
