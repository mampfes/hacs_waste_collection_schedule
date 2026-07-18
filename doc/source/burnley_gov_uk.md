# Burnley Council

Support for schedules provided by [Burnley Council](https://burnley.gov.uk).

Source for burnley.gov.uk services for the Burnley, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: burnley_gov_uk
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
    - name: burnley_gov_uk
      args:
        uprn: '100010341681'
```
