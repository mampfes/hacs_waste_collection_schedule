# Abfallwirtschaftsbetrieb Stadt Oldenburg (Oldb)

Support for schedules provided by [services.oldenburg.de](https://services.oldenburg.de/index.php?id=430).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_oldenburg_de
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
    - name: awb_oldenburg_de
      args:
        street: 'Friedhofsweg'
        house_number: '30'
```
