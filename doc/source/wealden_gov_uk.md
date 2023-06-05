# Wealden County Council

Support for schedules provided by [Wealden County Council](https://www.wealden.gov.uk/), serving the Wealden County, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wealden_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*


## Example using UPRN
```yaml
waste_collection_schedule:
    sources:
    - name: wealden_gov_uk
      args:
        uprn: "10094620272"
```


#### How to find your `UPRN`
Your uprn is the collection of numbers at the end of the url when viewing your collection schedule on the Wealden County Council web site.

For example:  _https://www.wealden.gov.uk/recycling-and-waste/bin-search/?uprn=100060117274_

Alternatively, you can discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.



