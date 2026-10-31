# Powys County Council

Support for schedules provided by [Powys County Council](https://en.powys.gov.uk).

Source for en.powys.gov.uk services for Powys

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: powys_gov_uk
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
    - name: powys_gov_uk
      args:
        postcode: SY16 2PQ
        uprn: '100100307820'
```

## How to get the source arguments

Enter your postcode (e.g. SY16 2PQ) and the Unique Property Reference Number (UPRN) of your property. You can find your UPRN at https://www.findmyaddress.co.uk/. Since the v3 pipeline migration, waste types use canonical, localised names, and the weekly recycling and food waste round is reported as two collections. Update filters, automations and customisations using the old labels.
