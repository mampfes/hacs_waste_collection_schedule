# West Suffolk Council

Support for schedules provided by [West Suffolk Council](https://westsuffolk.gov.uk/).

Source for West Suffolk Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: westsuffolk_gov_uk
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
    - name: westsuffolk_gov_uk
      args:
        uprn: 10090739388
```
