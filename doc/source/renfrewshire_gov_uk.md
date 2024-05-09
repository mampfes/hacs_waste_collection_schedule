# Renfrewshire Council

Support for schedules provided by [Renfrewshire Council](https://www.renfrewshire.gov.uk/article/2320/Check-your-bin-collection-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: renfrewshire_gov_uk
      args:
        postcode: POSTCODE
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**postcode**
*(string) (required)*

**uprn**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: renfrewshire_gov_uk
      args:
        postcode: "PA12 4AJ"
        uprn: "123034174"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
