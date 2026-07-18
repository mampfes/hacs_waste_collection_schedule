# AWB Oldenburg

Support for schedules provided by [AWB Oldenburg](https://www.oldenburg.de).

Source for 'Abfallwirtschaftsbetrieb Stadt Oldenburg (Oldb)'.

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
        street: Friedhofsweg
        house_number: 30
```
