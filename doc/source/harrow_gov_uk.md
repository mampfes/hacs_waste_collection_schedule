# London Borough of Harrow

Support for schedules provided by [London Borough of Harrow](https://www.harrow.gov.uk/).

Source for London Borough of Harrow.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: harrow_gov_uk
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
    - name: harrow_gov_uk
      args:
        uprn: '100021261713'
```
