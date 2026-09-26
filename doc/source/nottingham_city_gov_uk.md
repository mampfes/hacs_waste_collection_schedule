# Nottingham City Council

Support for schedules provided by [Nottingham City Council](https://nottinghamcity.gov.uk).

Source for nottinghamcity.gov.uk services for the city of Nottingham, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nottingham_city_gov_uk
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
    - name: nottingham_city_gov_uk
      args:
        uprn: '100031540175'
```
