# London Borough of Havering

Support for schedules provided by [London Borough of Havering](https://www.havering.gov.uk/).

Source for London Borough of Havering.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: havering_gov_uk
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
    - name: havering_gov_uk
      args:
        uprn: '100021403735'
```
