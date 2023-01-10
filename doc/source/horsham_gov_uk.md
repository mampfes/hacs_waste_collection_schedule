# Horsham District Council

Support for schedules provided by [Horsham District Council](https://www.horsham.gov.uk/waste-recycling-and-bins/household-bin-collections/check-your-bin-collection-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: horsham_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
_(string) (required)_

## Example using UPRN

```yaml
waste_collection_schedule:
  sources:
    - name: horsham_gov_uk
      args:
        uprn: "10013792881"
```

## How to get the source argument

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
