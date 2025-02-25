# Moyne Shire Council

Support for schedules provided by [Moyne Shire Council](https://www.moyne.vic.gov.au/Your-property/Waste-and-recycling/Kerbside-collection-dates).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: moyne_vic_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: moyne_vic_gov_au
      args:
        street_address: 1 Cox Street, PORT FAIRY, 3284
```

## How to get the source arguments

Visit the [Moyne Shire Council waste and recycling](https://www.moyne.vic.gov.au/Your-property/Waste-and-recycling/Kerbside-collection-dates) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.
