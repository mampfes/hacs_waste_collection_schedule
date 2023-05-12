# Aberdeenshire Council

Support for schedules provided by [Aberdeenshire Council](https://www.aberdeenshire.gov.uk/), serving Aberdeenshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: aberdeenshire_gov_uk
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
    - name: aberdeenshire_gov_uk
      args:
        uprn: "000151650618"
```


#### How to find your `UPRN`
Your uprn is the collection of numbers at the end of the url when viewing your collection schedule on the Aberdeenshire Councile web site.

For example:  _online.aberdeenshire.gov.uk/Apps/Waste-Collections/Routes.aspx?uprn=`000151650618`_

Alternatively, you can discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.



