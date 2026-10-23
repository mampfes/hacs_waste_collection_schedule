# South Tyneside Council

Support for schedules provided by [South Tyneside Council](https://southtyneside.gov.uk).

Source for southtyneside.gov.uk services for South Tyneside Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: southtyneside_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: southtyneside_gov_uk
      args:
        postcode: NE34 8RY
        uprn: '100000342955'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/.
