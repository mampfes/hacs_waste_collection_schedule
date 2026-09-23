# Mornington Peninsula Shire Council

Support for schedules provided by [Mornington Peninsula Shire Council](https://www.mornpen.vic.gov.au).

Source for Mornington Peninsula Shire Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mornpen_vic_gov_au
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
    - name: mornpen_vic_gov_au
      args:
        street_address: 305 Baldrys Rd Main Ridge VIC 3928
```
