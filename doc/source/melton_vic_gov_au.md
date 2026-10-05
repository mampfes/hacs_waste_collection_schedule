# Melton City Council

Support for schedules provided by [Melton City Council](https://www.melton.vic.gov.au).

Source for Melton City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: melton_vic_gov_au
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
    - name: melton_vic_gov_au
      args:
        street_address: 1 HIGH STREET MELTON 3337
```
