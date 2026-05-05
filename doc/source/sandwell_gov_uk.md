# Sandwell Metropolitan Borough Council

Support for schedules provided by [Sandwell Metropolitan Borough Council](https://www.sandwell.gov.uk/binday), serving the borough of Sandwell, UK.

This source retrieves household waste, recycling, food waste, and (where subscribed) garden waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sandwell_gov_uk
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
    - name: sandwell_gov_uk
      args:
        uprn: 10008535857
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providng your address details.