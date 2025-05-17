# Rugby Borough Council

Support for schedules provided by [Rugby Borough Council](https://www.rugby.gov.uk/), serving Rugby, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rugby_gov_uk
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
    - name: rugby_gov_uk
      args:
        uprn: "010010521297"
```


#### How to get the source argument
An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.



