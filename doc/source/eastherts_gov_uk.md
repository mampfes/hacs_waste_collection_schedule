# Waverley Borough Council

Support for schedules provided by [East Herts Council](https://www.eastherts.gov.uk/bins-waste-and-recycling), serving East Herts, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eastherts_gov_uk
      args:
        address_postcode: POST_CODE
        address_name_numer: HOUSE_NAME_NUMER,
        address_street: ADDRESS_STREET,
        street_town: STREET_TOWN
        version: 1

```

### Configuration Variables
You must supply enough address details for the search to find your property as the first match.

Test this out manually first at [East Herts Council](https://www.eastherts.gov.uk/bins-waste-and-recycling) if you are not sure which are needed.


**POST_CODE**  
*(string) (optional)*

**HOUSE_NAME_NUMER**  
*(string) (optional)*

**ADDRESS_STREET**  
*(string) (optional)*

**STREET_TOWN**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: eastherts_gov_uk
      args:
        post_code: "SG9 9AA"
        address_name_numer: "1 Trove House"
        address_street: "Baldock Road"
```
