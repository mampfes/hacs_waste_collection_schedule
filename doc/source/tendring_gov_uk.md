# Tendring District Council

Support for schedules provided by [Tendring District Council](https://www.tendringdc.gov.uk), Essex, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Essex, please continue to use the source for your current area as long as it's still working. New sources for the new North East Essex Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tendring_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**
*(string) (required)*

Your Unique Property Reference Number (UPRN).

## How to find your UPRN

1. Visit the [Tendring collection days checker](https://tendring-self.achieveservice.com/en/service/Rubbish_and_recycling_collection_days) and search for your address.
2. Alternatively, look up your address at [findmyaddress.co.uk](https://www.findmyaddress.co.uk/).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tendring_gov_uk
      args:
        uprn: "YOUR_UPRN_HERE"
```
