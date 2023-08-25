# East Renfrewshire Council

Support for schedules provided by [East Renfrewshire Council](https://www.eastrenfrewshire.gov.uk/bin-days).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: east_renfrewshire_gov_uk
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
    - name: east_renfrewshire_gov_uk
      args:
        postcode: "G78 2TJ"
        uprn: "131016859"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
