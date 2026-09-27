# Lichfield District Council

Support for schedules provided by [Lichfield District Council](https://lichfielddc.gov.uk).

Source for Lichfield District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lichfielddc_gov_uk
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
    - name: lichfielddc_gov_uk
      args:
        uprn: '100031695248'
```
