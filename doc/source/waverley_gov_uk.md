# Waverley Borough Council

Support for schedules provided by [Waverley Borough Council](https://waverley.gov.uk).

Source for www.waverley.gov.uk services for Waverley Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: waverley_gov_uk
      args:
        address_postcode: ADDRESS_POSTCODE
        address_name_numer: ADDRESS_NAME_NUMER
        address_street: ADDRESS_STREET
        street_town: STREET_TOWN
```

### Configuration Variables

**address_postcode**  
*(string) (required)*

**address_name_numer**  
*(string) (optional)*

**address_street**  
*(string) (optional)*

**street_town**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: waverley_gov_uk
      args:
        address_postcode: GU8 5QQ
        address_name_numer: '1'
        address_street: Gasden Drive
```
