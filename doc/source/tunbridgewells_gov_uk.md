# Tunbridge Wells

Support for schedules provided by [Tunbridge Wells](https://tunbridgewells.gov.uk/).

Source for Tunbridge Wells.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tunbridgewells_gov_uk
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
    - name: tunbridgewells_gov_uk
      args:
        uprn: '10090058289'
```
