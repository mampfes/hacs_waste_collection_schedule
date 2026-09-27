# Wakefield Council

Support for schedules provided by [Wakefield Council](https://wakefield.gov.uk).

Source for Wakefield.gov.uk services for Wakefield Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wakefield_gov_uk
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
    - name: wakefield_gov_uk
      args:
        uprn: '63024087'
```
