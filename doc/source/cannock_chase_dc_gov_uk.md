# Cannock Chase Council

Support for schedules provided by [Cannock Chase Council](https://www.cannockchasedc.gov.uk/residents/recycling-waste/waste-collection-check-your-dates), serving Cannock Chase, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cannock_chase_dc_gov_uk
      args:
        post_code: POST_CODE
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**post_code**<br>
*(string) (required)*

**uprn**<br>
*(string) (required)*


## Example using UPRN
```yaml
waste_collection_schedule:
    sources:
    - name: cannock_chase_dc_gov_uk
      args:
        post_code: "WS15 1DN"
        uprn: "100031640287"
```


## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.


