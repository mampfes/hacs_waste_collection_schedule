# East Lindsey District Council

Support for waste collection schedules provided by [East Lindsey District Council](https://www.e-lindsey.gov.uk), serving the East Lindsey district of Lincolnshire, UK.

The source returns refuse, mixed recycling, paper, weekly food waste, and
subscribed garden-waste collections when available for the property.

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
