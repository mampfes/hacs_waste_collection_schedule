# Guildford Borough Council

Support for schedules provided by [Guildford Borough Council](https://guildford.gov.uk).

Source for guildford.gov.uk services for Guildford, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: guildford_gov_uk
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
    - name: guildford_gov_uk
      args:
        uprn: '10007060305'
```
