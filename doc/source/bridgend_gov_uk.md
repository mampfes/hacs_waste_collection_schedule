# Bridgend County Borough Council

Support for schedules provided by [Bridgend County Borough Council](https://bridgendportal.azurewebsites.net/), serving the city of Bridgend, Wales, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: bridgend_gov_uk
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
    - name: bridgend_gov_uk
      args:
        uprn: "100100479873"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.