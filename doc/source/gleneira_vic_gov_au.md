# City of Glen Eira

Support for schedules provided by [City of Glen Eira](https://www.gleneira.vic.gov.au/our-city/in-your-area).

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

Visit the [City of Glen Eira](https://www.gleneira.vic.gov.au/our-city/in-your-area) page and search for your address, for example `4 Staniland Grove ELSTERNWICK VIC 3185`.

The address is resolved through the council's own address lookup before the collection days are requested, so commas, lower case suburbs and abbreviated street types (e.g. `Hwy` for `Highway`) are accepted as well. If what you enter matches more than one property, the error message lists the addresses to choose from.
