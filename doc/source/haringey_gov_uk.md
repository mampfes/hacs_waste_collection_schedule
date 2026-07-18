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
You can find your Unique Property Reference Number (UPRN) by going to https://www.findmyaddress.co.uk/search and entering in your address details.
