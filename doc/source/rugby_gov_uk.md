# Rugby Borough Council

Support for schedules provided by [Rugby Borough Council](https://www.rugby.gov.uk/).

Source for Rugby Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rugby_gov_uk
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
    - name: rugby_gov_uk
      args:
        uprn: 100070200377
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/ by entering your address details.
