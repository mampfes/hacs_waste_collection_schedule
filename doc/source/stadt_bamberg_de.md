# Bamberg (City/Stadt)

Support for schedules provided by [Bamberg (City/Stadt)](https://www.stadt.bamberg.de).

Source for Bamberg (City/Stadt).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_bamberg_de
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
    - name: stadt_bamberg_de
      args:
        street: "Gartenstra\xDFe"
        house_number: 2
```
