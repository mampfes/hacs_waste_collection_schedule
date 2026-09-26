# Nillumbik Shire Council

Support for schedules provided by [Nillumbik Shire Council](https://www.nillumbik.vic.gov.au).

Source for Nillumbik Shire Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nillumbik_vic_gov_au
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
    - name: nillumbik_vic_gov_au
      args:
        street_address: 11 Sunnyside Crescent, WATTLE GLEN, 3096
```
