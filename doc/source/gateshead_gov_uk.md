# Gateshead Council

Support for schedules provided by [Gateshead Council](https://www.gateshead.gov.uk).

Source for gateshead.gov.uk services for Gateshead

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gateshead_gov_uk
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
    - name: gateshead_gov_uk
      args:
        uprn: 100000058404
```

## How to get the source arguments

Enter the Unique Property Reference Number (UPRN) of your property. You can find it at https://www.findmyaddress.co.uk/. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
