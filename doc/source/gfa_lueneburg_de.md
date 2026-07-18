# GFA Lüneburg

Support for schedules provided by [GFA Lüneburg](https://www.gfa-lueneburg.de/).

Source for GFA Lüneburg.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gfa_lueneburg_de
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gfa_lueneburg_de
      args:
        city: Dahlem
        street: Hauptstr.
        house_number: 7
```

## How to get the source arguments

Make sure the address exactly matches the one auto-completed by the website form: https://www.gfa-lueneburg.de/service/abfuhrkalender.html
