# Renfrewshire Council

Support for schedules provided by [Renfrewshire Council](https://renfrewshire.gov.uk/).

Source for renfrewshire.gov.uk services for Renfrewshire

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: renfrewshire_gov_uk
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
    - name: renfrewshire_gov_uk
      args:
        uprn: '123033059'
```
