# Epping Forest District Council

Support for schedules provided by [Epping Forest District Council](https://www.eppingforestdc.gov.uk), Essex, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eppingforestdc_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**
*(string) (required)*

Your Unique Property Reference Number (UPRN).

## How to find your UPRN

1. Visit the [Epping Forest bin collection checker](https://eppingforestdc-self.achieveservice.com/service/Check_your_collection_day) and search for your address — your UPRN will appear in the URL or page.
2. Alternatively, look up your address at [findmyaddress.co.uk](https://www.findmyaddress.co.uk/).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eppingforestdc_gov_uk
      args:
        uprn: "100090495060"
```
