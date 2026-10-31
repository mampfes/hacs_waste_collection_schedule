# East Renfrewshire Council

Support for schedules provided by [East Renfrewshire Council](https://eastrenfrewshire.gov.uk).

Source for eastrenfrewshire.gov.uk services for East Renfrewshire

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: east_renfrewshire_gov_uk
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
    - name: east_renfrewshire_gov_uk
      args:
        postcode: G78 2TJ
        uprn: '131016859'
```

## How to get the source arguments

Enter your postcode and the Unique Property Reference Number (UPRN) of your property. You can find your UPRN at https://www.findmyaddress.co.uk/. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
