# Dover District Council

Support for schedules provided by [Dover District Council](https://www.dover.gov.uk).

Source for Dover District Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dover_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: dover_gov_uk
      args:
        uprn: 200002423404
```

## How to get the source arguments

Enter the Unique Property Reference Number (UPRN) of your property. You can find it at https://www.findmyaddress.co.uk/. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
