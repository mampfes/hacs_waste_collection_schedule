# North East Derbyshire District Council

Support for schedules provided by [North East Derbyshire District Council](https://www.ne-derbyshire.gov.uk).

Source for North East Derbyshire District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ne_derbyshire_gov_uk
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
    - name: ne_derbyshire_gov_uk
      args:
        uprn: '100030223463'
```

## How to get the source arguments

Find the UPRN of your property at https://www.findmyaddress.co.uk/. Your collection weekday and North/South calendar are looked up from it; the dates come from the council's bin collection dates page.
