# Ashfield District Council

Support for schedules provided by [Harlow Council](https://www.harlow.gov.uk/), serving Harlow district in Essex, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: harlow_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

### Configuration Variables

**uprn**<br>
*(string) (required)*


#### How to find your `UPRN`
An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
Otherwise you can inspect the web requests the Harlow Council website makes when entering in your postcode and then selecting your address.

## Example
```yaml
waste_collection_schedule:
    sources:
    - name: harlow_gov_uk
      args:
        uprn: 10023422690
```