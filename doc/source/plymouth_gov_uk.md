# Plymouth City Council

Support for schedules provided by [Plymouth City Council](https://www.plymouth.gov.uk/check-your-bin-day), serving Plymouth, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: plymouth_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*

This is required to unambiguously identify the property.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: plymouth
      args:
        uprn: "100040425325"

```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
