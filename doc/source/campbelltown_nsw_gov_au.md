# Campbelltown City Council (NSW)

Support for schedules provided by [Campbelltown City Council (NSW)](https://www.campbelltown.nsw.gov.au/).

Source for Campbelltown City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: campbelltown_nsw_gov_au
      args:
        street_name: STREET_NAME
        street_number: STREET_NUMBER
        post_code: POST_CODE
        suburb: SUBURB
```

### Configuration Variables

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

**post_code**  
*(string) (required)*

**suburb**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: campbelltown_nsw_gov_au
      args:
        post_code: '2566'
        suburb: Minto
        street_name: Brookfield Road
        street_number: '10'
```
