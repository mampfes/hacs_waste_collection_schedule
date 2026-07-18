# City of Kingston

Support for schedules provided by [City of Kingston](https://www.kingston.vic.gov.au).

Source for City of Kingston (VIC) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kingston_vic_gov_au
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
    - name: kingston_vic_gov_au
      args:
        street_number: 30C
        street_name: Oakes Avenue
        suburb: CLAYTON SOUTH
        post_code: '3169'
```
