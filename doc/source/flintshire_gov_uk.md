# Flintshire, United Kingdom

Support for schedules provided by [Flintshire, United Kingdom](https://flintshire.gov.uk/), serving Flintshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: flintshire_gov_uk
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
    - name: flintshire_gov_uk
      args:
        uprn: "100100211557"
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

Alternatively you can inspect your browsers traffic in the network section of the developer tools (F12 or right click -> inspect element) and look for a request to `https://digital.flintshire.gov.uk/FCC_BinDay/Home/Details2/200001744973` where `200001744973` is the UPRN.
