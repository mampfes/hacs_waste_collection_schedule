# Nillumbik Shire Council

Support for schedules provided by [Nillumbik Shire Council](https://www.nillumbik.vic.gov.au).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nillumbik_vic_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nillumbik_vic_gov_au
      args:
        street_address: 30 Crest Road, RESEARCH, 3095
```

## How to get the source arguments

Visit the [Nillumbik Shire Council waste and recycling](https://www.nillumbik.vic.gov.au/Residents/Waste-and-recycling/Bin-collection/Check-my-bin-day) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.