# Blackburn with Darwen Borough Council

Support for schedules provided by [Blackburn with Darwen Borough Council](https://blackburn.gov.uk/).

Source for mybins.blackburn.gov.uk services for Blackburn with Darwen Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: blackburn_gov_uk
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
    - name: blackburn_gov_uk
      args:
        uprn: '10091617919'
```
