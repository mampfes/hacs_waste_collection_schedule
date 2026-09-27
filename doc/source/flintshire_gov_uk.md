# Flintshire

Support for schedules provided by [Flintshire](https://flintshire.gov.uk/).

Source for Flintshire, United Kingdom.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: flintshire_gov_uk
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
    - name: flintshire_gov_uk
      args:
        uprn: 100100211557
```
