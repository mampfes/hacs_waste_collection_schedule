# Redbridge Council

Support for schedules provided by [Redbridge Council](https://www.redbridge.gov.uk/), serving Redbridge, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: redbridge_gov_uk
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
    - name: redbridge_gov_uk
      args:
        uprn: 10034922090
```


#### How to find your `UPRN`
Your uprn is the collection of numbers at the end of the url when downloading a collection calendar for your collection schedule on the Redbridge web site.

For example:  _https://my.redbridge.gov.uk/RecycleRefuse/GetFile?uprn=`10034922090`_

Alternatively, you can discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.



