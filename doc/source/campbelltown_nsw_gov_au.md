# Cambelltown City Council

Support for schedules provided by [Cambelltown City Council Waste and Recycling](https://www.campbelltown.nsw.gov.au/ServicesandFacilities/WasteandRecycling).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: campbelltown_nsw_gov_au
      args:
        post_code: POST_CODE
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**post_code**<br>
*(string) (required)*

**suburb**<br>
*(string) (required)*

**street_name**<br>
*(string) (required)*

**street_number**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: campbelltown_nsw_gov_au
      args:
        post_code: 2566
        suburb: Minto
        street_name: Brookfield Road
        street_number: 10
```

## How to get the source arguments

Visit the [Cambelltown City Council Waste and Recycling](https://www.campbelltown.nsw.gov.au/ServicesandFacilities/WasteandRecycling) page and search for your address. The arguments should exactly match the results shown for Post Code, Suburb, Street and number portion of the Property.
