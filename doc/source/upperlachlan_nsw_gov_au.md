# Upper Lachlan Shire Council

Support for schedules provided by [Upper Lachlan Shire Council](https://upperlachlan.nsw.gov.au/services/waste/).

Waste collections for Upper Lachlan Shire Council, NSW.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: upperlachlan_nsw_gov_au
      args:
        route: ROUTE
```

### Configuration Variables

**route**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: upperlachlan_nsw_gov_au
      args:
        route: Crookwell - Monday recycling
```

## How to get the source arguments

Choose your serviced locality. In Crookwell, choose your street's Monday or Tuesday recycling round; this does not change other bin days. Check your route with council if unsure. Lost River supplies recycling only because the calendar does not specify its other services. Dates follow the council PDF. Only published dates are returned. Next year's calendar is included once linked by council; until then the latest available calendar is used without extending its dates. Separate service-disruption notices are not included.
