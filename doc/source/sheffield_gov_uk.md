# Sheffield City Council

Support for schedules provided by [Sheffield City Council](https://sheffield.gov.uk/).

Source for waste collection services from Sheffield City Council (SCC)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sheffield_gov_uk
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
    - name: sheffield_gov_uk
      args:
        uprn: 100050938234
```
