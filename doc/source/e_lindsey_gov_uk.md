# East Lindsey District Council

Garden waste dates are read from the council's public, property-selected PDF
calendar. This includes the reduced winter schedule and dates in the following
calendar year. The season start date shown by the lookup is not treated as the
next collection. No garden collections are added for properties without a garden
waste calendar.

Support for waste collection schedules provided by [East Lindsey District Council](https://www.e-lindsey.gov.uk), serving the East Lindsey district of Lincolnshire, UK.

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
Your Unique Property Reference Number (UPRN). Find yours at [findmyaddress.co.uk](https://www.findmyaddress.co.uk/) or [finders.io](https://www.finders.io/).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: e_lindsey_gov_uk
      args:
        uprn: "100030786099"
```
