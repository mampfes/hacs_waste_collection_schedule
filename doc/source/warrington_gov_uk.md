# Warrington Borough Council

Support for schedules provided by [Warrington Borough Council](https://www.warrington.gov.uk).

Source for warrington.gov.uk services for Warrington Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: warrington_gov_uk
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
    - name: warrington_gov_uk
      args:
        uprn: '100010309878'
```
