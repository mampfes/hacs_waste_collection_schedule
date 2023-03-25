# Wigan Council

Support for schedules provided by [City of Doncaster Council](https://www.doncaster.gov.uk/services/bins-recycling-waste), serving the city of Doncaster, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: doncaster_gov_uk
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
    - name: doncaster_gov_uk
      args:
        uprn: "100050701118"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.