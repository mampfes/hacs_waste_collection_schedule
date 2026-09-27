# Newcastle Under Lyme Borough Council

Support for schedules provided by [Newcastle Under Lyme Borough Council](https://www.newcastle-staffs.gov.uk).

Source for waste collection services for Newcastle Under Lyme Borough Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: newcastle_staffs_gov_uk
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
    - name: newcastle_staffs_gov_uk
      args:
        uprn: 100031744129
```
