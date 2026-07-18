# Stadtreinigung Gießen

Support for schedules provided by [Stadtreinigung Gießen](https://stadtreinigung.giessen.de).

Source for Stadtreinigung Gießen waste collection schedule.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_giessen_de
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
    - name: stadtreinigung_giessen_de
      args:
        street: Achstattring
        house_number: '1'
```
