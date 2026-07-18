# Hemar (ichisystem.eu)

Support for schedules provided by [Hemar (ichisystem.eu)](https://harmonogram.ichisystem.eu/hemar/).

Source for the Hemar waste collection schedule platform (harmonogram.ichisystem.eu) used by several Polish municipalities. This deployment runs on the same underlying "SEPAN"/ICHI System platform as sepan_remondis_pl and alba_com_pl.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ichisystem_eu
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
    - name: ichisystem_eu
      args:
        city: Pobiedziska
        street: Boczna
        house_number: '2'
```

## How to get the source arguments

Open https://harmonogram.ichisystem.eu/hemar/ and pick your city, street, and house number from the dropdowns. Use those exact values for the city, street, and house_number arguments (matching is case-insensitive).
