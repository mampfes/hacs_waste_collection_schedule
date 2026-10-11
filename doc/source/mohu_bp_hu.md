# MOHU Budapest

Support for schedules provided by [MOHU Budapest](https://www.mohubudapest.hu).

Source script for www.mohubudapest.hu

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mohu_bp_hu
      args:
        district: DISTRICT
        street: STREET
        house_number: HOUSE_NUMBER
        verify: VERIFY
```

### Configuration Variables

**district**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**verify**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mohu_bp_hu
      args:
        district: 1114
        street: "Szent Gell\xE9rt t\xE9r"
        house_number: 3
```

## How to get the source arguments

Choose your district (its postcode, e.g. 1114), street and house number as the calendar at https://www.mohubudapest.hu/hulladeknaptar writes them. `verify` is no longer used.
