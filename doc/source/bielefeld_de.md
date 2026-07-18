# Bielefeld

Support for schedules provided by [Bielefeld](https://bielefeld.de).

Source for Stadt Bielefeld.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bielefeld_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
        address_suffix: ADDRESS_SUFFIX
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**address_suffix**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bielefeld_de
      args:
        street: "Eckendorfer Stra\xDFe"
        house_number: 57
```
