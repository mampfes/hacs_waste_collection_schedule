# North Herts Council

Support for schedules provided by [North Herts Council](https://www.north-herts.gov.uk/).

Source for www.north-herts.gov.uk services for North Herts Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: northherts_gov_uk
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
    - name: northherts_gov_uk
      args:
        address_postcode: SG4 9QY
        address_name_numer: '26'
        address_street: BENSLOW RISE
```
