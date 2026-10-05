# Moyne Shire Council

Support for schedules provided by [Moyne Shire Council](https://www.moyne.vic.gov.au).

Source for Moyne Shire Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: moyne_vic_gov_au
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
    - name: moyne_vic_gov_au
      args:
        street_address: 1 Cox Street, PORT FAIRY, 3284
```
