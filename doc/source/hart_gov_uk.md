# Hart District Council

Support for schedules provided by [Hart District Council](https://www.hart.gov.uk/).

Source for hart.gov.uk services for Hart District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hart_gov_uk
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
    - name: hart_gov_uk
      args:
        uprn: '100060420702'
```
