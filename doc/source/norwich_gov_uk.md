# North Norfolk District Council

Support for the next collection day provided by [Norwich City Council](https://maps.norwich.gov.uk/mynorwich/), serving Norwich, UK.

Note that Norwich City Council does not provide a schedule, only the next collection day.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: norwich_gov_uk
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
    - name: norwich_gov_uk
      args:
        uprn: "100090924499"
```

## How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
