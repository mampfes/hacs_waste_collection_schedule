# Abfallwirtschaftsbetrieb Stadt Oldenburg (Oldb)

Support for schedules provided by [www.oldenburg.de](https://www.oldenburg.de/startseite/leben-umwelt/awb/abfall-a-z/abfuhrkalender.html).

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

**street**  
*(string) (required)*

**house_number**  
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
