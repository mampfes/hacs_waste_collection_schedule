# AHK Heidekreis

Support for schedules provided by [AHK Heidekreis](https://www.ahk-heidekreis.de).

Source for AHK Heidekreis, Germany (ahk-heidekreis.de)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ahk_heidekreis_de
      args:
        city: CITY
        postcode: POSTCODE
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**postcode**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ahk_heidekreis_de
      args:
        city: Munster
        postcode: '29633'
        street: Wagnerstr.
        house_number: 10-18
```
