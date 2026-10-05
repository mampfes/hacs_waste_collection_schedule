# East Suffolk Council

Support for schedules provided by [East Suffolk Council](https://www.eastsuffolk.gov.uk).

Source for East Suffolk Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eastsuffolk_gov_uk
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
    - name: eastsuffolk_gov_uk
      args:
        uprn: '100091126543'
```

## How to get the source arguments

Find your UPRN by visiting https://my.eastsuffolk.gov.uk/service/Bin_collection_dates_finder and searching for your address. Your UPRN can also be found at https://www.findmyaddress.co.uk/.
