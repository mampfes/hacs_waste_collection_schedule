# Swindon Borough Council

Support for schedules provided by [Swindon Borough Council](https://swindon.gov.uk/).

If collection data is available for the address provided, it will return household and recycling waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: swindon_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

Only the UPRN should be supplied in the arguments.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: swindon_gov_uk
      args:
        uprn: 100121147490
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providng your address details.