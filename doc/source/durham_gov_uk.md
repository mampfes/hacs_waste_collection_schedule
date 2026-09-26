# Durham County Council

Support for schedules provided by [Durham County Council](https://durham.gov.uk).

Source for Durham County Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: durham_gov_uk
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
    - name: durham_gov_uk
      args:
        uprn: '100110414978'
```
