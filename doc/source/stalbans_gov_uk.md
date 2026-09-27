# St Albans City & District Council

Support for schedules provided by [St Albans City & District Council](https://stalbans.gov.uk).

Source for St Albans City & District Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stalbans_gov_uk
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
    - name: stalbans_gov_uk
      args:
        uprn: 100081132201
```
