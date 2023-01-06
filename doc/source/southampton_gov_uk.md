# Southampton City Council

Support for schedules provided by [Southampton City Council](https://southampton.gov.uk/)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: southampton_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*

This is required to unambiguously identify the property.

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: southampton_gov_uk
      args:
        uprn: "100060685712"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
