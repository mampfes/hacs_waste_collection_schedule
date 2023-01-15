# Waverley Borough Council

Support for schedules provided by [Waverley Borough Council](https://www.waverley.gov.uk/Services/Bins-and-recycling/Rubbish-and-recycling-collections/Check-bin-collection-day), serving Borough of Waverley, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: waverley_gov_uk
      args:
        address_postcode: POST_CODE
        address_name_numer: HOUSE_NAME_NUMER,
        address_street: ADDRESS_STREET,
        street_town: STREET_TOWN
        version: 1

```

### Configuration Variables
You must supply enough address details for the search to find your property as the first match.

Test this out manually first at [Waverley Borough Council](https://www.waverley.gov.uk/Services/Bins-and-recycling/Rubbish-and-recycling-collections/Check-bin-collection-day) if you are not sure which are needed.


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
    - name: waverley_gov_uk
      args:
        post_code: "GU8 5QQ"
        address_name_numer: "1"
        address_street: "Gasden Drive"
```
