# East Hampshire District Council

Support for bin collection schedules provided by [East Hampshire District Council](https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: easthants_gov_uk
      args:
        uprn: 1710041123
```

## Configuration variables

**uprn**
*(string or integer) (required)* — The property's Unique Property Reference Number. Search for the property on the council's [map](https://maps.easthants.gov.uk/) and use the value shown as the Unique Property Ref.

The source follows the selected East Hampshire property to its official refuse/recycling and garden-waste calendar PDFs and returns the dates published there. Food waste is not currently included because the council's calendar page says the household food-waste service is planned for October 2026.

## Returned waste types

The source returns:

- Rubbish
- Recycling
- Glass
- Garden Waste, when the property has a garden-waste calendar
