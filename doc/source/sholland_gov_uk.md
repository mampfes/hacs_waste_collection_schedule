# South Holland District Council

Support for schedules provided by [South Holland District Council](https://www.sholland.gov.uk/).

Source for South Holland District Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sholland_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sholland_gov_uk
      args:
        uprn: 10002546801
        postcode: PE11 2FR
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/. The postcode is not used by the council's lookup but is kept for existing configurations.
