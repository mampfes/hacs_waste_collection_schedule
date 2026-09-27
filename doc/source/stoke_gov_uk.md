# Stoke-on-Trent

Support for schedules provided by [Stoke-on-Trent](https://www.stoke.gov.uk/).

Source for Stoke-on-Trent

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stoke_gov_uk
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
    - name: stoke_gov_uk
      args:
        uprn: '3455011383'
```
