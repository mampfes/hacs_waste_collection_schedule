# City of Casey

Support for schedules provided by [City of Casey](https://www.casey.vic.gov.au/).

Source for the City of Casey rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: casey_vic_gov_au
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
    - name: casey_vic_gov_au
      args:
        street_address: 55 Victor Crescent NARRE WARREN VIC 3805
```

## How to get the source arguments

Visit the City of Casey "Find your bin collection day" page (https://www.casey.vic.gov.au/find-your-bin-collection-day) and search for your address. Enter the full street address exactly as the autocomplete shows it, without commas and with the suburb and state in capitals, e.g. 55 Victor Crescent NARRE WARREN VIC 3805. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
