# Gold Coast City Council

Support for schedules provided by [Gold Coast City Council](https://www.goldcoast.qld.gov.au).

Source for Gold Coast Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: goldcoast_qld_gov_au
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
    - name: goldcoast_qld_gov_au
      args:
        street_address: 50 Millaroo Dr Helensvale
```
