# Stonnington City Council

Support for schedules provided by [Stonnington City Council](https://www.stonnington.vic.gov.au).

Source for Stonnington City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stonnington_vic_gov_au
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
    - name: stonnington_vic_gov_au
      args:
        street_address: 500 Chapel Street, South Yarra
```
