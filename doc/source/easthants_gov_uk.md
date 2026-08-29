# East Hampshire District Council

Support for schedules provided by [East Hampshire District Council](https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar), serving East Hampshire, UK.

The source can look up a property's current calendars from its UPRN. This automatically includes subscribed garden waste when the council lists a garden calendar for the property. Manual calendar numbers remain available as a fallback.

## Configuration via configuration.yaml

### Recommended: UPRN lookup

```yaml
waste_collection_schedule:
    sources:
    - name: easthants_gov_uk
      args:
        uprn: 1710041123
```

### Manual calendar numbers

```yaml
waste_collection_schedule:
    sources:
    - name: easthants_gov_uk
      args:
        calendar_number: 16
        garden_calendar_number: 1
```

### Configuration Variables

**uprn**
*(String or integer) (optional)* The property's Unique Property Reference Number. When supplied, this takes precedence over manual calendar numbers and automatically follows the bin and garden calendar links assigned by the council.

**calendar_number**
*(Integer) (optional)* The bin calendar number assigned to your address. Required when `uprn` is not supplied.

**garden_calendar_number**
*(Integer) (optional)* The numeric part of the G1-G10 garden waste calendar number assigned to subscribed households. For example, enter `1` for calendar G1. This is only needed with manual calendar-number configuration.

## How to find the configuration values

Open the council's [Find your bin calendar](https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar) page and use the map near the bottom to select your address. The map displays its **Unique Property Ref**, bin calendar, and any garden waste calendar.

## Returned waste types

- Rubbish
- Recycling
- Glass
- Garden waste, when the property has a garden waste calendar or one is configured manually
