# Mosman Council

Support for schedules provided by [Mosman Council](https://mosman.nsw.gov.au/).

Source for Mosman Council, NSW, Australia

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mosman_nsw_gov_au
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
    - name: mosman_nsw_gov_au
      args:
        address: 12 Shadforth Street
```
