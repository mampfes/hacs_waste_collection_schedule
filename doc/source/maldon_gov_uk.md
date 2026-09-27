# Maldon District Council

Support for schedules provided by [Maldon District Council](https://www.maldon.gov.uk/).

Source for www.maldon.gov.uk services for Maldon, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: maldon_gov_uk
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
    - name: maldon_gov_uk
      args:
        uprn: '200000917928'
```
