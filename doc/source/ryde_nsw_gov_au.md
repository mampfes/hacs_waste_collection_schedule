# City of Ryde (NSW)

Support for schedules provided by [City of Ryde](https://www.ryde.nsw.gov.au/Environment-and-Waste/Waste-and-Recycling).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ryde_nsw_gov_au
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
    - name: ryde_nsw_gov_au
      args:
        post_code: 2112
        suburb: Ryde
        street_name: Victoria Road
        street_number: 504
```

## How to get the source arguments

Visit the [City of Ryde Waste and Recycling](https://www.ryde.nsw.gov.au/Environment-and-Waste/Waste-and-Recycling) page, follow the quick link to *Check my collection day*, and search for your address. The street address arguments used to configure hacs_waste_collection_schedule should exactly match the street address shown in the autocomplete result.

## How this integration uses City of Ryde's APIs
Two API calls are currently needed to retrieve waste collection schedule results from Campbelltown Council:
1. The address search API at https://www.ryde.nsw.gov.au/api/v1/myarea/search
2. The waste services API at https://www.ryde.nsw.gov.au/ocapi/Public/myarea/wasteservices

This integration does the following:
1. Calls the address search API to retrieve the "location ID" for the given location. Eg. https://www.ryde.nsw.gov.au/api/v1/myarea/search?keywords=504+Victoria+Road%2C+Ryde
2. Retrieves waste/collection info from the waste services API using the "location ID" retrieved in step #1. Eg. https://www.ryde.nsw.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=619ef4ca-45e2-4866-a55b-165e6d563943&ocsvclang=en-AU
3. Parses the HTML returned by the waste services API in step #2 to extract the data

# Similarities with other sources

For future work it's good to note that City of Ryde uses the same APIs as Campbelltown City Council & Blacktown City Council, to the point I was able to copy and paste their files with minimal modification.