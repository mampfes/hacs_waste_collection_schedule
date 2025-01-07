# North Norfolk District Council

Support for schedules provided by [North Norfolk District Council](https://forms.north-norfolk.gov.uk/xforms/Address/Show/CollectionAddress), serving North Norfolk, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: north_norfolk_gov_uk
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
    - name: north_norfolk_gov_uk
      args:
        uprn: "100090880632"
```

## How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
`
