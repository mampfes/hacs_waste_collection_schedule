# Melton Borough Council

Support for schedules provided by [Melton Borough Council](https://www.melton.gov.uk/waste-and-recycling/), serving Melton District, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: melton_gov_uk
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
    - name: melton_gov_uk
      args:
        uprn: "100030544791"
```

## How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
`
