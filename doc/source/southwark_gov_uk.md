# London Borough of Southwark

Support for schedules provided by [London Borough of Southwark](https://www.southwark.gov.uk/).

Source for London Borough of Southwark waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: southwark_gov_uk
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
    - name: southwark_gov_uk
      args:
        uprn: '200003455089'
```
