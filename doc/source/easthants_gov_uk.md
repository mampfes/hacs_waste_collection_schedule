# East Hampshire District Council

Support for schedules provided by [East Hampshire District Council](https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar), serving East Hampshire, UK.

The council publishes numbered calendars for rubbish (green bin), recycling (black bin), and glass box collections. The source automatically follows the current PDF linked for the selected calendar number.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: easthants_gov_uk
      args:
        calendar_number: 16
```

### Configuration Variables

**calendar_number**
*(Integer) (required)* The bin calendar number assigned to your address.

## How to find your calendar number

Open the council's [Find your bin calendar](https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar) page. If you do not already know your calendar number, use the map near the bottom of the page to find your address.
