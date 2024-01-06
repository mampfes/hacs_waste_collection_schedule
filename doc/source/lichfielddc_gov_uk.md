# Lichfield District Council

Support for schedules provided by [Lichfield District Council](https://www.lichfielddc.gov.uk/), serving Lichfield, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: lichfielddc_gov_uk
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
    - name: lichfielddc_gov_uk
      args:
        uprn: "100031705547"
```


#### How to find your `UPRN`
Your uprn is the collection of numbers at the end of the url when viewing your collection schedule on the Lichfield District Council web site.

Alternatively, you can discover what your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.



