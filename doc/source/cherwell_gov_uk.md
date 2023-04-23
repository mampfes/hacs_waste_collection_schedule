# Cherwell District Council

Support for schedules provided by [Cherwell District Council](https://www.cherwell.gov.uk/info/10/rubbish-and-recycling), serving Cherwell District Council, North Oxfordshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cherwell_gov_uk
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
    - name: cherwell_gov_uk
      args:
        uprn: "100120758315"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.