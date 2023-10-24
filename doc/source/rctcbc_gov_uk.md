# Rhondda Cynon Taf County Borough Council

Support for schedules provided by [Rhondda Cynon Taf County Borough Council](https://www.rctcbc.gov.uk/), Wales, UK.



## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rctcbc_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**
_(string) (optional)_

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: rctcbc_gov_uk
      args:
        uprn: "10024274791"
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and searching for your address details.
