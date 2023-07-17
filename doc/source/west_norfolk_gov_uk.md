# Borough Council of King's Lynn & West Norfolk

Support for schedules provided by [Borough Council of King's Lynn & West Norfolk](https://www.west-norfolk.gov.uk), serving Borough Council of King's Lynn & West Norfolk, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: west_norfolk_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*


#### How to find your `UPRN`
An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.

## Example
```yaml
waste_collection_schedule:
    sources:
    - name: west_norfolk_gov_uk
      args:
        uprn: "100090989776"
```
