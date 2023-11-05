# Blacktown City Council (NSW)

Support for schedules provided by [Blacktown City Council Waste and Recycling](https://www.blacktown.nsw.gov.au/Services/Waste-services-and-collection/Waste-collection-days).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: blacktown_nsw_gov_au
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
    - name: blacktown_nsw_gov_au
      args:
        post_code: 2770
        suburb: Emerton
        street_name: Helena Ave
        street_number: 80
```

## How to get the source arguments

Visit the [Blacktown City Council Waste Collection Days](https://www.blacktown.nsw.gov.au/Services/Waste-services-and-collection/Waste-collection-days) page, follow the quick link to *Check my collection day*, and search for your address. The street address arguments used to configure hacs_waste_collection_schedule should exactly match the street address shown in the autocomplete result.

## How this integration uses Blacktown Council's APIs
Two API calls are currently needed to retrieve waste collection schedule results from Blacktown Council:
1. The address search API at https://www.blacktown.nsw.gov.au/api/v1/myarea/search
2. The waste services API at https://www.blacktown.nsw.gov.au/ocapi/Public/myarea/wasteservices

This integration does the following:
1. Calls the address search API to retrieve the "location ID" for the given location. Eg. https://www.blacktown.nsw.gov.au/api/v1/myarea/search?keywords=80+Helena+Ave+Emerton+NSW+2770
2. Retrieves waste/collection info from the waste services API using the "location ID" retrieved in step #1. Eg. https://www.blacktown.nsw.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=6177cbfa-6f35-4fbf-9208-63d4dde7f048&ocsvclang=en-AU
3. Parses the HTML returned by the waste services API in step #2 to extract the data


# Similarities with other sources

For future work it's good to note that Blacktown City Council uses the same APIs as Campbelltown City Council, to the point I was able to copy and paste their files with minimal modification.
 