# Solihull Council

Support for schedules provided by [Solihull Council](https://www.solihull.gov.uk/).

Source for Solihull Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: solihull_gov_uk
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
    - name: solihull_gov_uk
      args:
        uprn: 100070994046
```
