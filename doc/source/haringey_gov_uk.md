# Haringey Council

Support for schedules provided by [Haringey Council](https://www.haringey.gov.uk/), serving Haringey, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: haringey_gov_uk
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
    - name: haringey_gov_uk
      args:
        uprn: "100021209182"
```


#### How to find your `UPRN`
Your uprn is the collection of numbers at the end of the url when viewing your collection schedule on the Haringey Council web site.

For example:  _wastecollections.haringey.gov.uk/property/`000151650618`_

Alternatively, you can discover what your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.



