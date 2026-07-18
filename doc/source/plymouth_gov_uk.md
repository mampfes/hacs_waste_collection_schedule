# Plymouth City Council

Support for schedules provided by [Plymouth City Council](https://www.plymouth.gov.uk/).

Source for waste collection services for Plymouth City Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: plymouth_gov_uk
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
    - name: plymouth_gov_uk
      args:
        uprn: 100040429524
```
