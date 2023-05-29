# East Herts Council

Support for schedules provided by [East Herts Council](https://www.eastherts.gov.uk/bins-waste-and-recycling), serving East Herts, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eastherts_gov_uk
      args:
        address_postcode: POST_CODE
        address_name_number: HOUSE_NAME_NUMBER
        version: 1

```

### Configuration Variables
You only need to supply the house name/number and post code.

Test this out manually first at [East Herts Council](https://www.eastherts.gov.uk/bins-waste-and-recycling) if you are not sure which are needed.


**ADDRESS_POSTCODE**  
*(string) (required)*

**ADDRESS_NAME_NUMBER**  
*(string) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: eastherts_gov_uk
      args:
        address_postcode: "SG9 9AA"
        address_name_number: "1"
```
