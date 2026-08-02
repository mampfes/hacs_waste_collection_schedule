# East Suffolk Council

Support for schedules provided by [East Suffolk Council](https://www.eastsuffolk.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eastsuffolk_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**
*(string) (required)*

Your Unique Property Reference Number (UPRN).

## How to find your UPRN

1. Visit the [East Suffolk bin collection dates finder](https://my.eastsuffolk.gov.uk/service/Bin_collection_dates_finder) and search for your address.
2. Alternatively, look up your address at [findmyaddress.co.uk](https://www.findmyaddress.co.uk/).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eastsuffolk_gov_uk
      args:
        uprn: "YOUR_UPRN_HERE"
```
