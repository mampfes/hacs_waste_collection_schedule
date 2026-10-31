# Sunderland City Council

Support for schedules provided by [Sunderland City Council](https://www.sunderland.gov.uk/bindays?ccp=true).

Source for Sunderland City Council bin collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sunderland_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**postcode**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sunderland_gov_uk
      args:
        postcode: SR4 7PU
        address: 191 Cleveland Road
```

## How to get the source arguments

Enter the postcode and property address from the Sunderland bin day checker. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
