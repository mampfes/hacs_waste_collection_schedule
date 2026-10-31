# New Forest District Council

Support for schedules provided by [New Forest District Council](https://www.newforest.gov.uk).

Source for newforest.gov.uk services for New Forest District Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: newforest_gov_uk
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
    - name: newforest_gov_uk
      args:
        postcode: SO40 8XX
        uprn: 100060514912
```

## How to get the source arguments

Enter your postcode (e.g. SO40 8XX) and the Unique Property Reference Number (UPRN) of your property. You can find your UPRN at https://www.findmyaddress.co.uk/. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
