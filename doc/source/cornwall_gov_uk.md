# Cornwall Council

Support for schedules provided by [Cornwall Council](https://www.cornwall.gov.uk/), serving Truro, Bodmin, St Austell and much more

If collection data is available for the address provided, it will return food, rubbish and recycling waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cornwall_gov_uk
      args:
        postcode: POSTCODE
        uprn:     UPRN
```

### Configuration Variables

**postcode**<br>
*(string) (optional)*

**hournameornumber**<br>
*(string) (optional)*

**uprn**<br>
*(string) (optional)*

Either the postcode and housenameornumber or the UPRN should be supplied in the arguments

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: cornwall_gov_uk
      args:
        postcode: TR261SP
        housenameornumber: 7
        uprn: 100040118005
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providng your address details. 
