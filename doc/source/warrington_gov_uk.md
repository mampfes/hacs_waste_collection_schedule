# Warrington Borough Council

Support for schedules provided by [Warrington Borough Council](https://www.warrington.gov.uk/), serving Warrington Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: warrington_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*


#### How to find your `UPRN`
An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.

## Example using UPRN
```yaml
waste_collection_schedule:
    sources:
    - name: warrington_gov_uk
      args:
        uprn: 100010309878
```
