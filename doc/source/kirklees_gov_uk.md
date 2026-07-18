# Kirklees Council

Support for schedules provided by [Kirklees Council](https://www.kirklees.gov.uk).

Source for waste collections for Kirklees Council (my.kirklees.gov.uk)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kirklees_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
        predict: PREDICT
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

**predict**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kirklees_gov_uk
      args:
        uprn: '83074265'
        postcode: HD9 7HA
```
