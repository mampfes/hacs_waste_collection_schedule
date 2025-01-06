# North Norfolk District Council

Support for schedules provided by [Dartford Borough Council](https://www.dartford.gov.uk/waste-recycling/collection-day), serving Darford, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: dartford_gov_uk
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
    - name: dartford_gov_uk
      args:
        uprn: "100060862889"
```

## How to find your `UPRN`

Your UPRN is displayed in the top left corner of the Dartford website when you are viewing your collection schedule.
Alternatively, an easy wasy to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
`
