# City of Glen Eira

Support for schedules provided by [City of Glen Eira](https://www.gleneira.vic.gov.au/).

Source for the Glen Eira City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gleneira_vic_gov_au
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
    - name: gleneira_vic_gov_au
      args:
        street_address: 4 Staniland Grove ELSTERNWICK VIC 3185
```

## How to get the source arguments

Visit the [Glen Eira City Council](https://www.gleneira.vic.gov.au/our-city/in-your-area) "Find your bin collection day" page and search for your address, for example: 4 Staniland Grove ELSTERNWICK VIC 3185. The address is resolved through the council's own address lookup, so commas, lower case suburbs and abbreviated street types (e.g. "Hwy" for "Highway") are accepted as well. The council shows the next collection of each bin. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
