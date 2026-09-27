# Cherwell District Council

Support for schedules provided by [Cherwell District Council](https://www.cherwell.gov.uk).

Cherwell District Council North Oxfordshire, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cherwell_gov_uk
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
    - name: cherwell_gov_uk
      args:
        uprn: '100120758315'
```
