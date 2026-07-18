# Elmbridge Borough Council

Support for schedules provided by [Elmbridge Borough Council](https://www.elmbridge.gov.uk).

Source for waste collection services for Elmbridge Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: elmbridge_gov_uk
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
    - name: elmbridge_gov_uk
      args:
        uprn: 10013119164
```
