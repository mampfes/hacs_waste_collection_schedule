# Unley City Council (SA)

Support for schedules provided by [Unley City Council Waste and Recycling](https://www.unley.sa.gov.au/Bins-pets-parking/Waste-recycling/Rubbish-collection-dates).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: unley_sa_gov_au
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
    - name: unley_sa_gov_au
      args:
        post_code: 5061
        suburb: Malvern
        street_name: Wattle Street
        street_number: 176
```

## How to get the source arguments

Visit the [Unley City Council Waste and Recycling](https://www.unley.sa.gov.au/Bins-pets-parking/Waste-recycling/Rubbish-collection-dates) page, follow the quick link to *Check my collection day*, and search for your address. The street address arguments used to configure hacs_waste_collection_schedule should exactly match the street address shown in the autocomplete result.

## How this integration uses Campbelltown Council's APIs
Two API calls are currently needed to retrieve waste collection schedule results from Campbelltown Council:
1. The address search API at https://www.unley.sa.gov.au/api/v1/myarea/search
2. The waste services API at https://www.unley.sa.gov.au/ocapi/Public/myarea/wasteservices

This integration does the following:
1. Calls the address search API to retrieve the "location ID" for the given location. Eg. https://www.unley.sa.gov.au/api/v1/myarea/search?keywords=176%20wattle%20street%20malvern%205061
2. Retrieves waste/collection info from the waste services API using the "location ID" retrieved in step #1. Eg. https://www.unley.sa.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=21f0cda5-8602-4162-b488-0d0f452a821a&ocsvclang=en-AU
3. Parses the HTML returned by the waste services API in step #2 to extract the data
