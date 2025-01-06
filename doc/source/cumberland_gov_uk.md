# Cumberland Council

Support for schedules provided by [Cumberland Council](https://waste.cumberland.gov.uk/renderform?t=25&k=E43CEB1FB59F859833EF2D52B16F3F4EBE1CAB6A), serving Cumberland, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cumberland_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
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
    - name: cumberland_gov_uk
      args:
        postcode: "CA28 7QS"
        uprn: "100110319463"
```

## How to find your UPRN
An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.