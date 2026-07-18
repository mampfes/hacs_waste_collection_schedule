# Kleszczewo/Kostrzyn

Support for schedules provided by [Kleszczewo/Kostrzyn](https://www.puk-zys.pl/index.php).

Source for Kleszczewo/Kostrzyn commune garbage collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zys_harmonogram_pl
      args:
        commune_name: COMMUNE_NAME
        city: CITY
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**commune_name**  
*(string) (required)*

**city**  
*(string) (required)*

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zys_harmonogram_pl
      args:
        city: Komorniki
        street_name: Komorniki
        street_number: 93/2
        commune_name: Kleszczewo
```

## How to get the source arguments

Enter the commune (e.g. 'Kleszczewo'), then your city, street and house number exactly as they appear in the lookup at https://www.puk-zys.pl/index.php. Matching is case-insensitive.
