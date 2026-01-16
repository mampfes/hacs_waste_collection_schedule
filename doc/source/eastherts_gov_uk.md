# East Herts Council

Support for schedules provided by [East Herts Council](https://www.eastherts.gov.uk/bins-waste-and-recycling), serving East Herts, UK.

## Configuration via configuration.yaml
```yaml
waste_collection_schedule:
    sources:
    - name: eastherts_gov_uk
      args:
        uprn: UPRN
        address_postcode: POST_CODE
        address_name_number: HOUSE_NAME_NUMBER
```

### Configuration Variables
In 2025, East Herts changed their website to a _uprn_-based search function. The older _house name/number_ and _postcode_ format has been retained for backward compatibility.

You can supply args as one of these two formats:
- The uprn only (preferred method)
- Both the house name/number and post code (legacy method)

<br>

**UPRN**  
*(string) (optional)*

**ADDRESS_POSTCODE**  
*(string) (optional)*

**ADDRESS_NAME_NUMBER**  
*(string) (optional)*


## Examples
The following examples are equivalent

```yaml
# preferred method
waste_collection_schedule:
    sources:
    - name: eastherts_gov_uk
      args:
        uprn: "10033104539"
```

```yaml
# legacy method
waste_collection_schedule:
    sources:
    - name: eastherts_gov_uk
      args:
        address_postcode: "SG9 9AA"
        address_name_number: "1"
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.