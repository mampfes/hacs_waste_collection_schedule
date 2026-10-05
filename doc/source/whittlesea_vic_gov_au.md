# Whittlesea City Council

Support for schedules provided by [Whittlesea City Council](https://www.whittlesea.vic.gov.au/My-Neighbourhood).

Source for Whittlesea Council (VIC) rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: whittlesea_vic_gov_au
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
    - name: whittlesea_vic_gov_au
      args:
        street_address: 25 Ferres Boulevard, South Morang 3752
```
