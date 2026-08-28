# East Hampshire District Council

Support for schedules provided by [East Hampshire District Council](https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar), serving East Hampshire, UK.

The council publishes numbered calendars for rubbish (green bin), recycling (black bin), glass box, and subscribed garden waste collections. The source automatically follows the current PDFs linked for the selected calendar numbers.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: easthants_gov_uk
      args:
        calendar_number: 16
        garden_calendar_number: 1
```

### Configuration Variables

**calendar_number**
*(Integer) (required)* The bin calendar number assigned to your address.

**garden_calendar_number**
*(Integer) (optional)* The numeric part of the G1-G10 garden waste calendar number assigned to subscribed households. For example, enter `1` for calendar G1.

## How to find your calendar number

Open the council's [Find your bin calendar](https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar) page. If you do not already know your calendar numbers, use the map near the bottom of the page to find your address. Garden waste subscribers should also enter the numeric part of their G1-G10 garden waste calendar number.
