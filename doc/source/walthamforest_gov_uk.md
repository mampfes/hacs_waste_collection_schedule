# Waltham Forest

Support for schedules provided by [Waltham Forest](https://walthamforest.gov.uk/).

Source for Waltham Forest.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: walthamforest_gov_uk
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
    - name: walthamforest_gov_uk
      args:
        uprn: '200001421821'
```
