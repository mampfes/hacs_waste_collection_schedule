# Reading Council

Support for schedules provided by [Reading Council](https://www.reading.gov.uk/).

If collection data is available for the address provided, it will return rubbish and recycling waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: reading_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**postcode**
_(string) (optional)_

**housenameornumber**
_(string|int) (optional)_

**uprn**
_(string) (optional)_

Either the postcode _and_ housenameornumber or the UPRN should be supplied in the arguments

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: reading_gov_uk
      args:
        uprn: "310027679"
```

```yaml
waste_collection_schedule:
  sources:
    - name: reading_gov_uk
      args:
        postcode: "RG31 5PN"
        housenameornumber: "65"
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providing your address details.
