# East Northamptonshire and Wellingborough

Support for schedules provided by [East Northamptonshire and Wellingborough](east-northamptonshire.gov.uk).

Source for East Northamptonshire and Wellingborough

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: east_northamptonshire_gov_uk
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
    - name: east_northamptonshire_gov_uk
      args:
        uprn: '100031046896'
```

## How to get the source arguments

Find the UPRN of your property, e.g. on <https://www.findmyaddress.co.uk/>.
