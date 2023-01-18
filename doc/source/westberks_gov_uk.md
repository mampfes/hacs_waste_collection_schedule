# West Berkshire Council

Support for schedules provided by [West Berkshire Council](https://www.westberks.gov.uk/).

If collection data is available for the address provided, it will return rubbish and recycling waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: westberks_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
_(string) (optional)_

**hournameornumber**  
_(string) (optional)_

**uprn**  
_(string) (optional)_

Either the postcode _and_ housenameornumber or the UPRN should be supplied in the arguments

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: westberks_gov_uk
      args:
        uprn: "100080241094"
```

```yaml
waste_collection_schedule:
  sources:
    - name: westberks_gov_uk
      args:
        postcode: "RG18 4QU"
        housenameornumber: "6"
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providing your address details.
