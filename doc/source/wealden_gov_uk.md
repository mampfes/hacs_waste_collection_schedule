# Wealden District Council

Support for schedules provided by [Wealden District Council](https://www.wealden.gov.uk).

Source for Wealden City services for Wealden District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wealden_gov_uk
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
    - name: wealden_gov_uk
      args:
        uprn: '10094620272'
```
