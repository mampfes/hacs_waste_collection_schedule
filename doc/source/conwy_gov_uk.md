# Conwy County Borough Council

Support for schedules provided by [Conwy County Borough Council](https://www.conwy.gov.uk/).

Source for Conwy County Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: conwy_gov_uk
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
    - name: conwy_gov_uk
      args:
        uprn: 50000009637
```
