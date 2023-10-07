# Mansfield Shire Council

Support for schedules provided by [Mansfield Shire Council](https://www.mansfield.vic.gov.au/Community/Residents/Waste-Recycling/Check-My-Bin-Day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mansfield_vic_gov_au
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
    - name: mansfield_vic_gov_au
      args:
        street_address: 95 High Street, Mansfield
```

## How to get the source arguments

Visit the [Mansfield Shire Council waste and recycling](https://www.mansfield.vic.gov.au/Community/Residents/Waste-Recycling/Check-My-Bin-Day) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.
