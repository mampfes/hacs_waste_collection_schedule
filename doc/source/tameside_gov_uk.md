# Tameside Metropolitan Borough Council

Support for schedules provided by [Tameside Metropolitan Borough Council](https://tameside.gov.uk/), UK.


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tameside_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*


## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: tameside_gov_uk
      args:
        postcode: "M34 6AG"
        uprn: "100011601683"
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providng your address details.
