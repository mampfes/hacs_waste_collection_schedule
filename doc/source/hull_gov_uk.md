# Hull City Council

Support for schedules provided by [Hull City Council](https://hull.gov.uk/).

Source for Hull City Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hull_gov_uk
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
    - name: hull_gov_uk
      args:
        uprn: 21095794
```
