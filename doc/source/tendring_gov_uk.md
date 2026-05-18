# Tendring District Council

Support for schedules provided by [Tendring District Council](https://www.tendringdc.gov.uk), Essex, UK.

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
