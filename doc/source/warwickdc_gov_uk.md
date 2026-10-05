# Warwick District Council

Support for schedules provided by [Warwick District Council](https://www.warwickdc.gov.uk).

Source for Warwick District Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: warwickdc_gov_uk
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
    - name: warwickdc_gov_uk
      args:
        uprn: '100070260258'
```
