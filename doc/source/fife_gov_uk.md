# Fife Council

Support for schedules provided by [Fife Council](https://www.fife.gov.uk), serving Fife Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fife_gov_uk
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
    - name: fife_gov_uk
      args:
        uprn: "320069189"
        
```

### How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
Otherwise you can inspect the web requests the Fife Council website makes when entering in your postcode and then selecting your address.
