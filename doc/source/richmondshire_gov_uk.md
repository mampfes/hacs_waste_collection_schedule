# Richmondshire District Council

Support for schedules provided by [Richmondshire District Council](https://www.richmondshire.gov.uk/bins-and-recycling/), serving North Yorkshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: richmondshire_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_IDENTIFICATION_NUMBER

```

### Configuration Variables

**UPRN**  
*(integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: richmondshire_gov_uk
      args:
        uprn: 200001767082
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details. Or you can visit the Richmondshire page and use the address search. Right-click your entry in the house dropdown, choose Inspect, and copy the UPRN from the value