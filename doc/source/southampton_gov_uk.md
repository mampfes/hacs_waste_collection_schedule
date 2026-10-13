# Southampton City Council

Support for schedules provided by [Southampton City Council](https://southampton.gov.uk).

Source for southampton.gov.uk services for Southampton City Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: southampton_gov_uk
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
    - name: southampton_gov_uk
      args:
        uprn: '100060731893'
```
