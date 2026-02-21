# West Lothian Council

Support for schedules provided by [West Lothian Council](https://www.westlothian.gov.uk/bin-collections).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: westlothian_gov_uk
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
    - name: westlothian_gov_uk
      args:
        postcode: "EH55 8FJ"
        uprn: "135051417"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
