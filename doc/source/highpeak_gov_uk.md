# High Peak Borough Council

Support for schedules provided by [High Peak Borough Council](https://www.highpeak.gov.uk/).

Source for High Peak Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: highpeak_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: highpeak_gov_uk
      args:
        postcode: SK23 6BQ
        uprn: 10010724045
```
