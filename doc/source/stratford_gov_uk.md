# Stratford District Council

Support for schedules provided by [Stratford District Council](https://stratford.gov.uk).

Source for Stratford District Council and their 123+ bin collection system

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stratford_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stratford_gov_uk
      args:
        uprn: '100071513500'
```
