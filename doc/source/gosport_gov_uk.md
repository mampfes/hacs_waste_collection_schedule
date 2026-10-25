# Gosport Borough Council

Support for schedules provided by [Gosport Borough Council](https://www.gosport.gov.uk).

Source for Gosport Borough Council waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gosport_gov_uk
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
    - name: gosport_gov_uk
      args:
        postcode: PO12 4RL
        uprn: '37020212'
```

## How to get the source arguments

Go to https://www.gosport.gov.uk/refuserecyclingdays, enter your postcode, and select your address. Use the Whitespace property reference shown next to your address in the dropdown as uprn. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
