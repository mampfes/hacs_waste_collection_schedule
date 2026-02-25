# Arun District Council

Support for schedules provided by [Arun District Council](https://www.arun.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: arun_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**
*(string) (required)*

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: arun_gov_uk
      args:
        uprn: "010091569392"
```

#### How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
