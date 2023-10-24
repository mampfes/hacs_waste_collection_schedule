# Cheshire West and Chester Council

Support for schedules provided by [Cheshire West and Chester Council](https://www.cheshirewestandchester.gov.uk/).

If collection data is available for the address provided, it will return rubbish and recycling waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cheshire_west_and_chester_gov_uk
      args:
        uprn:     UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: cheshire_west_and_chester_gov_uk
      args:
        uprn: 100010030086
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providng your address details.
