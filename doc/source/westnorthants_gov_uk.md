# West Northamptonshire council

Support for schedules provided by [West Northamptonshire council](https://www.northnorthants.gov.uk/), serving West Northamptonshire council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: westnorthants_gov_uk
      args:
        uprn: "UPRN"
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: westnorthants_gov_uk
      args:
        uprn: "28058314"
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

Or by inspection the webtraffic of your browser while filling out the form you will see a request to <https://api.westnorthants.digital/openapi/v1/unified-waste-collections/28058314> where `28058314` is your UPRN.
