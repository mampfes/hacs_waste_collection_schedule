# Dover District Council

Support for schedules provided by [Dover District Council](https://www.dover.gov.uk), serving Dover, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: dover_gov_uk
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
    - name: dover_gov_uk
      args:
        uprn: "200002423404"        
```

## How to get the source argument

You can find your UPRN when visiting the <https://collections.dover.gov.uk/> website and searching for your address. You can now see your UPRN in the address bar of your browser. e.g. `https://collections.dover.gov.uk/property/200002423404`, where `200002423404` is the UPRN.

### Getting your UPRN with an external service

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
