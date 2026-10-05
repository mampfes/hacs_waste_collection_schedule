# Macedon Ranges Shire Council

Support for schedules provided by [Macedon Ranges Shire Council](https://www.mrsc.vic.gov.au).

Source for Macedon Ranges Shire Council rubbish collection.

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
        street_address: 20 Victoria Street, Macedon
```
