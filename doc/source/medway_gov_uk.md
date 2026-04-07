# Medway Council

Support for schedules provided by [Medway Council](https://www.medway.gov.uk/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: medway_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**
_(string|int) (optional)_

**postcode**
_(string) (optional)_

**housenameornumber**
_(string|int) (optional)_

Either the UPRN or both the postcode _and_ housenameornumber should be supplied in the arguments.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: medway_gov_uk
      args:
        uprn: "100062390963"
```

```yaml
waste_collection_schedule:
  sources:
    - name: medway_gov_uk
      args:
        postcode: "ME4 4AY"
        housenameornumber: "194-198"
```

## How to find your UPRN

You can find your UPRN by entering your postcode at [Medway's collection day checker](https://www.medway.gov.uk/homepage/45/check_collection_day). Alternatively, go to [Find My Address](https://www.findmyaddress.co.uk/) and provide your address details.
