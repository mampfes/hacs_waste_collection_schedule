# Mid Devon District Council

Support for schedules provided by [Mid Devon District Council](https://www.middevon.gov.uk).

Source for waste collection services for Mid Devon District Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mid_devon_gov_uk
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
    - name: mid_devon_gov_uk
      args:
        uprn: 100040359199
```
