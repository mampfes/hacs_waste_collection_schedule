# Sandwell Council

Support for schedules provided by [Sandwell Council](https://my.sandwell.gov.uk/).

Source for waste collection services for Sandwell Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sandwell_gov_uk
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
    - name: sandwell_gov_uk
      args:
        uprn: '10008535856'
```
