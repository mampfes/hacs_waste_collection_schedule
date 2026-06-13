# Epping Forest District Council

Support for schedules provided by [Epping Forest District Council](https://www.eppingforestdc.gov.uk), Essex, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Essex, please continue to use the source for your current area as long as it's still working. New sources for the new West Essex Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

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
