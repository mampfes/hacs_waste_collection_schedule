# North Yorkshire Council - Hambleton

Support for schedules provided by [North Yorkshire Council - Hambleton](https://northyorks.gov.uk), serving Hambleton North Yorkshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: northyorks_hambleton_gov_uk
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
    - name: northyorks_hambleton_gov_uk
      args:
        uprn: "010070735142"
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
