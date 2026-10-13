# East Lindsey District Council

Support for schedules provided by [East Lindsey District Council](https://www.e-lindsey.gov.uk).

Source for East Lindsey District Council waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: e_lindsey_gov_uk
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
    - name: e_lindsey_gov_uk
      args:
        uprn: '100030786099'
```

## How to get the source arguments

Find your UPRN using a tool like findmyaddress.co.uk or finders.io.
