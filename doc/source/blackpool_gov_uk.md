# Blackpool Council

Support for schedules provided by [Blackpool Council](https://blackpool.gov.uk).

Source for blackpool.gov.uk services for Blackpool Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: blackpool_gov_uk
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
    - name: blackpool_gov_uk
      args:
        postcode: FY1 4DZ
        uprn: '100010802829'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/ by entering your address. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
