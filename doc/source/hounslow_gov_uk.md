# London Borough of Hounslow

Support for schedules provided by [London Borough of Hounslow](https://hounslow.gov.uk).

Source for London Borough of Hounslow.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hounslow_gov_uk
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
    - name: hounslow_gov_uk
      args:
        uprn: 10090801236
```
