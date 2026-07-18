# eThekwini Municipality

Support for schedules provided by [eThekwini Municipality](https://www.durban.gov.za/page/refuse-collection-schedules).

Source for eThekwini Municipality / Durban refuse collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: durban_gov_za
      args:
        region: REGION
        area: AREA
        recycling_in_even_week: RECYCLING_IN_EVEN_WEEK
```

### Configuration Variables

**region**  
*(string) (required)*

**area**  
*(string) (required)*

**recycling_in_even_week**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: durban_gov_za
      args:
        region: outer_west
        area: hillcrest
        recycling_in_even_week: true
```

## How to get the source arguments

Visit the <a href='https://www.durban.gov.za/page/refuse-collection-schedules'>refuse collection schedules</a> page, open your region's DOCX file, and find your suburb or area under the weekday column. Use the matching region (e.g. outer_west, north, south_central, north_central, inner_west, south) and collection-area slug shown in that document. For 'Recycling collected on even ISO weeks', check your last recycling collection date to determine whether it fell on an even or odd ISO week number.
