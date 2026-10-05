# Salford City Council

Support for schedules provided by [Salford City Council](https://www.salford.gov.uk).

Source for bin collection services for Salford City Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: salford_gov_uk
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
    - name: salford_gov_uk
      args:
        uprn: '100011404886'
```
