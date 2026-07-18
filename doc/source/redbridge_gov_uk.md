# Redbridge Council

Support for schedules provided by [Redbridge Council](https://redbridge.gov.uk).

Source for redbridge.gov.uk services for Redbridge Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: redbridge_gov_uk
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
    - name: redbridge_gov_uk
      args:
        uprn: 10034922090
```
