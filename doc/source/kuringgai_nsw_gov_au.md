# Ku-ring-gai Council

Support for schedules provided by [Ku-ring-gai Council Waste and Recycling](https://www.krg.nsw.gov.au/Community/Waste-and-recycling/Bins-and-collection-days).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kuringgai_nsw_gov_au
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
    - name: kuringgai_nsw_gov_au
      args:
        post_code: 2070
        suburb: LINDFIELD
        street_name: Wolseley Road
        street_number: 42
```

## How to get the source arguments

Visit the [Ku-ring-gai Council Waste and Recycling](https://www.krg.nsw.gov.au/Community/Waste-and-recycling/Bins-and-collection-days) page and search for your address. The arguments should exactly match the results shown for Post Code, Suburb, Street and number portion of the Property.
