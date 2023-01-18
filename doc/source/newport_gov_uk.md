# Newport City Council

Support for schedules provided by [Newport City Council](https://www.newport.gov.uk/), serving Newport in Wales, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: newport_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*


#### How to find your `UPRN`
An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
Otherwise you can inspect the web requests the Newport City Council website makes when entering in your postcode and then selecting your address.

## Example
```yaml
waste_collection_schedule:
    sources:
    - name: newport_gov_uk
      args:
        uprn: 100100688837
```