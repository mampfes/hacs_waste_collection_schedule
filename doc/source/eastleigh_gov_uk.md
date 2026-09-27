# Eastleigh Borough Council

Support for schedules provided by [Eastleigh Borough Council](https://eastleigh.gov.uk).

Source for Eastleigh Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eastleigh_gov_uk
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
    - name: eastleigh_gov_uk
      args:
        uprn: 100060319000
```
