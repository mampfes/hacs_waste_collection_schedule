# City of Marion

Support for schedules provided by [City of Marion](https://www.marion.sa.gov.au).

Source for City of Marion (South Australia) kerbside bin collections.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: marion_sa_gov_au
      args:
        calendar: CALENDAR
        collection_day: COLLECTION_DAY
```

### Configuration Variables

**calendar**  
*(string) (required)*

**collection_day**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: marion_sa_gov_au
      args:
        calendar: B
        collection_day: Monday
```

## How to get the source arguments

Open the kerbside bin collection calendar linked from https://www.marion.sa.gov.au/services-we-offer/waste-and-recycling/bin-collection-and-calendar. Calendar A and calendar B each list their suburbs under the collection weekday; choose the calendar and weekday listing your suburb. In Hallett Cove the map on calendar B shows your area.
