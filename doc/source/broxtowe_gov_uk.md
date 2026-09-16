# Broxtowe Borough Council

Support for schedules provided by [Broxtowe Borough Council](https://www.broxtowe.gov.uk/).

Source for Broxtowe Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: broxtowe_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: broxtowe_gov_uk
      args:
        uprn: 100031343805
        postcode: NG9 2NL
```
