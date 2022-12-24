# Macedon Ranges Shire Council

Support for schedules provided by [Macedon Ranges Shire Council](https://www.mrsc.vic.gov.au/Live-Work/Bins-Rubbish-Recycling/Bins-and-collection-days/Bin-collection-days).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mrsc_vic_gov_au
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
    - name: mrsc_vic_gov_au
      args:
        street_address: 45 Aitken Street, Gisborne
```

## How to get the source arguments

Visit the [Macedon Ranges Shire Council waste and recycling](https://www.mrsc.vic.gov.au/Live-Work/Bins-Rubbish-Recycling/Bins-and-collection-days/Bin-collection-days) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.
