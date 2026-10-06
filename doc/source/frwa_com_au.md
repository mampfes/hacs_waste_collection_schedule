# Fleurieu Regional Waste Authority

Support for schedules provided by [Fleurieu Regional Waste Authority](https://fleurieuregionalwasteauthority.com.au).

Source script for fleurieuregionalwasteauthority.com.au

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: frwa_com_au
      args:
        name_or_number: NAME_OR_NUMBER
        street: STREET
        district: DISTRICT
```

### Configuration Variables

**name_or_number**  
*(string) (required)*

**street**  
*(string) (required)*

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: frwa_com_au
      args:
        name_or_number: '42'
        street: WISHART CRESCENT
        district: ENCOUNTER BAY
```

## How to get the source arguments

Visit [FRWA collection calendar](https://fleurieuregionalwasteauthority.com.au/collection-calendar-downloads) and search for your street. Use the name/number, street name and district name as they appear when your collection schedule is being displayed.
