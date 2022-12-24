# North Somerset Council

Support for schedules provided by [North Somerset Council](https://www.n-somerset.gov.uk/), serving Clevedon, Nailsea, Portishead and Weston super Mare, along with numerous villages.

If collection data is available for the address provided, it will return food, rubbish and recycling waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: nsomerset_gov_uk
      args:
        postcode: POSTCODE
        uprn:     UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: nsomerset_gov_uk
      args:
        postcode: BS231UJ
        uprn: 24009468
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providng your address details. Otherwise you can inspect the source code on the [North Somerset waste collection](https://forms.n-somerset.gov.uk/Waste/CollectionSchedule) website after entering your postcode.
