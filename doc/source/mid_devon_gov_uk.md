# Mid Devon District Council

Support for schedules provided by [Mid Devon District Council](https://www.middevon.gov.uk/).

If collection data is available for the address provided, it will return rubbish and recycling waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: mid_devon_gov_uk
      args:
        uprn:     UPRN
```

### Configuration Variables

**uprn** _(string) (required)_  
Your Unique Property Reference Number (UPRN).

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: mid_devon_gov_uk
      args:
        uprn: 100040359199
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providing your address details.
