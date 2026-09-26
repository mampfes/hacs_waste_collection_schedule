# Bedford Borough Council

Support for schedules provided by [Bedford Borough Council](https://bedford.gov.uk).

Source for bedford.gov.uk services for Bedford Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bedford_gov_uk
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
    - name: bedford_gov_uk
      args:
        uprn: '100080009302'
```
