# Gwynedd

Support for schedules provided by [Gwynedd](https://www.gwynedd.gov.uk/).

Source for Gwynedd.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gwynedd_gov_uk
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
    - name: gwynedd_gov_uk
      args:
        uprn: 200003177805
```
