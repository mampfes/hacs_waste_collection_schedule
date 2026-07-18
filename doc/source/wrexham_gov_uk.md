# Wrexham County Borough Council

Support for schedules provided by [Wrexham County Borough Council](https://www.wrexham.gov.uk/).

Source for Wrexham County Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wrexham_gov_uk
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
    - name: wrexham_gov_uk
      args:
        uprn: '100100940408'
```
