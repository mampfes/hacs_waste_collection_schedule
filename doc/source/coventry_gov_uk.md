# Coventry City Council

Support for schedules provided by [Coventry City Council](https://www.coventry.gov.uk/).

Source for waste collection services for Coventry City Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: coventry_gov_uk
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
    - name: coventry_gov_uk
      args:
        uprn: '100070666040'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/ by searching for your address.
