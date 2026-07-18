# Aberdeen City Council

Support for schedules provided by [Aberdeen City Council](https://www.aberdeencity.gov.uk/).

Source script for the Aberdeen City Council bin collection calendar (integration.aberdeencity.gov.uk Granicus Firmstep self-service form).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aberdeencity_gov_uk
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
    - name: aberdeencity_gov_uk
      args:
        uprn: '9051064786'
```
