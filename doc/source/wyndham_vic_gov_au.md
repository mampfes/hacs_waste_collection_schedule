# Wyndham City Council, Melbourne

Support for schedules provided by [Wyndham City Council, Melbourne](https://wyndham.vic.gov.au).

Source for Wyndham City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wyndham_vic_gov_au
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
    - name: wyndham_vic_gov_au
      args:
        street_address: 3-19 Parkvista Drive TRUGANINA 3029
```

## How to get the source arguments

Enter your address as the council's bin day lookup on https://www.wyndham.vic.gov.au shows it, e.g. '3-19 Parkvista Drive TRUGANINA 3029'. An unknown address lists similar ones.
