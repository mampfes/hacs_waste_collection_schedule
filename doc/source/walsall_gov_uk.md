# Walsall Council

Support for schedules provided by [Walsall Council](https://www.walsall.gov.uk/).

Source for waste collection services from Walsall Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: walsall_gov_uk
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
    - name: walsall_gov_uk
      args:
        uprn: '100071103746'
```
