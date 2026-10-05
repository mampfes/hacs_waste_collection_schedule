# Amber Valley Borough Council

Support for schedules provided by [Amber Valley Borough Council](https://ambervalley.gov.uk).

Source for ambervalley.gov.uk services for Amber Valley Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ambervalley_gov_uk
      args:
        uprn: UPRN
        predict: PREDICT
```

### Configuration Variables

**uprn**  
*(string) (required)*

**predict**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ambervalley_gov_uk
      args:
        uprn: '100030011612'
        predict: true
```
