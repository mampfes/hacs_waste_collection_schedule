# Runnymede Borough Council

Support for schedules provided by [Runnymede Borough Council](https://www.runnymede.gov.uk/bin-collection-day), serving Runnymede, Surrey, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: runnymede_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: runnymede_gov_uk
      args:
        uprn: "100061482004"
```

## How to get the source argument

Find the UPRN of your address using [https://www.findmyaddress.co.uk/search](https://www.findmyaddress.co.uk/search).
