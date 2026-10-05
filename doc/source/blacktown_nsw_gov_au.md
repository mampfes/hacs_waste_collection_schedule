# Blacktown City Council (NSW)

Support for schedules provided by [Blacktown City Council (NSW)](https://www.blacktown.nsw.gov.au/).

Source for Blacktown City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: blacktown_nsw_gov_au
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
    - name: blacktown_nsw_gov_au
      args:
        post_code: '2766'
        suburb: Rooty Hill
        street_name: Learmonth St
        street_number: 13-15
```
