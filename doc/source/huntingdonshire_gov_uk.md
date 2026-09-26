# Huntingdonshire District Council

Support for schedules provided by [Huntingdonshire District Council](https://www.huntingdonshire.gov.uk).

Source for Huntingdonshire.gov.uk services for Huntingdonshire District Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: huntingdonshire_gov_uk
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
    - name: huntingdonshire_gov_uk
      args:
        uprn: '100090123510'
```
