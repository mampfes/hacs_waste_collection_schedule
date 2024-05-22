# North Ayrshire Council

Support for schedules provided by [North Ayrshire Council](https://www.north-ayrshire.gov.uk/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: north_ayrshire_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: north_ayrshire_gov_uk
      args:
        uprn: "126043248"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.