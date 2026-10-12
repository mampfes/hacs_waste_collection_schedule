# East Hampshire District Council

Support for schedules provided by [East Hampshire District Council](https://www.easthants.gov.uk).

Waste collection schedules for East Hampshire District Council.

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: easthants_gov_uk
      args:
        garden_calendar_number: GARDEN_CALENDAR_NUMBER
        uprn: UPRN
```

### Using calendar_number

```yaml
waste_collection_schedule:
  sources:
    - name: easthants_gov_uk
      args:
        garden_calendar_number: GARDEN_CALENDAR_NUMBER
        calendar_number: CALENDAR_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**calendar_number**  
*(string) (alternative)*

**garden_calendar_number**  
*(string) (optional)*

Provide one of: `uprn` or `calendar_number`.

## Example

### Using calendar_number

```yaml
waste_collection_schedule:
  sources:
    - name: easthants_gov_uk
      args:
        garden_calendar_number: 1
        calendar_number: 16
```

## How to get the source arguments

Open https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar. Use the map near the bottom of the page to find your address and its Unique Property Ref, then enter that as the UPRN; the council then supplies your bin and garden calendars itself. Alternatively, enter the calendar number shown on that page (for example 16 for 'Calendar 16') and, if you have a garden waste subscription, the numeric part of your garden calendar (for example 1 for 'G1').
