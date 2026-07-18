# East Cambridgeshire District Council

Support for schedules provided by [East Cambridgeshire District Council](https://www.eastcambs.gov.uk).

Source for eastcambs.gov.uk, East Cambridgeshire District Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eastcambs_gov_uk
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
    - name: eastcambs_gov_uk
      args:
        uprn: 10002601730
```
