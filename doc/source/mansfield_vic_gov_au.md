# Mansfield Shire Council

Support for schedules provided by [Mansfield Shire Council](https://www.mansfield.vic.gov.au).

Source for Mansfield Shire Council rubbish collection.

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
        street_address: 1064 Mansfield-Woods Point Road MANSFIELD VIC 3722
```

## How to get the source arguments

Search your address on the [Mansfield Shire Council bin day page](https://www.mansfield.vic.gov.au/community/residents/waste-recycling/check-my-bin-day) and enter it as shown in the autocomplete result, e.g. '3 Curia Street MANSFIELD VIC 3722'.
