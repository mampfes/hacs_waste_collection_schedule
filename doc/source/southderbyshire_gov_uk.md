# South Derbyshire District Council

Support for schedules provided by [South Derbyshire District Council](https://www.southderbyshire.gov.uk/our-services/recycling-bins-and-waste/bin-collection-dates), serving the
district of South Derbyshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: southderbyshire_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: southderbyshire_gov_uk
      args:
        uprn: "100030233745"
```

## How to get the uprn argument above

The UPRN code for your property is not easy to extract from the South Derbyshire District Council website so we recommend using [FindMyAddress](https://www.findmyaddress.co.uk/search). Search using your address and it will return the UPRN for your property to use with this integration.
