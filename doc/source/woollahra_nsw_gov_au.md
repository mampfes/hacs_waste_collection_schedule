# Woollahra Municipal Council (NSW)

Support for schedules provided by [Woollahra Municipal Council (NSW)](https://www.woollahra.nsw.gov.au/).

Source for Woollahra Municipal Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: woollahra_nsw_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: woollahra_nsw_gov_au
      args:
        address: 13 Paddington Street PADDINGTON NSW 2021
```
