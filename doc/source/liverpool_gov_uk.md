# Liverpool City Council

Support for schedules provided by [Liverpool City Council](https://www.liverpool.gov.uk).

Source for liverpool.gov.uk services for Liverpool City

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: liverpool_gov_uk
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
    - name: liverpool_gov_uk
      args:
        uprn: '38148233'
```
