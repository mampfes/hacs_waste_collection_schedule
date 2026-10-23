# Wigan Council

Support for schedules provided by [Wigan Council](https://wigan.gov.uk).

Source for wigan.gov.uk services for Wigan Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wigan_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wigan_gov_uk
      args:
        postcode: WN5 9BH
        uprn: '100011821616'
```
