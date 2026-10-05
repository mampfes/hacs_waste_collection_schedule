# Mansfield District Council

Support for schedules provided by [Mansfield District Council](https://mansfield.gov.uk).

Source for mansfield.gov.uk services for Mansfield District, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mansfield_gov_uk
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
    - name: mansfield_gov_uk
      args:
        uprn: '10091487039'
```
