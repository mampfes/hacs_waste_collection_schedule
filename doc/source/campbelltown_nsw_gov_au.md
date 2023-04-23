# Cambelltown City Council (NSW)

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

**post_code**  
*(string) (required)*

**suburb**  
*(string) (required)*

**street_name**  
*(string) (required)*

**street_number**  
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

Visit the [Cambelltown City Council Waste and Recycling](https://www.campbelltown.nsw.gov.au/ServicesandFacilities/WasteandRecycling) page, follow the quick link to *Check my collection day*, and search for your address. The street address arguments used to configure hacs_waste_collection_schedule should exactly match the street address shown in the autocomplete result.

## How this integration uses Campbelltown Council's APIs
Two API calls are currently needed to retrieve waste collection schedule results from Campbelltown Council:
1. The address search API at https://www.campbelltown.nsw.gov.au/api/v1/myarea/search
2. The waste services API at https://www.campbelltown.nsw.gov.au/ocapi/Public/myarea/wasteservices

This integration does the following:
1. Calls the address search API to retrieve the "location ID" for the given location. Eg. https://www.campbelltown.nsw.gov.au/api/v1/myarea/search?keywords=10%20brookfield%20road%20minto%202566
2. Retrieves waste/collection info from the waste services API using the "location ID" retrieved in step #1. Eg. https://www.campbelltown.nsw.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=401ee13b-b04c-4948-82e4-09d274c479a0&ocsvclang=en-AU
3. Parses the HTML returned by the waste services API in step #2 to extract the data
