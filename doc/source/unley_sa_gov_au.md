# Unley City Council (SA)

Support for schedules provided by [Unley City Council (SA)](https://www.unley.sa.gov.au/).

Source for Unley City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: unley_sa_gov_au
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
    - name: unley_sa_gov_au
      args:
        post_code: '5061'
        suburb: Malvern
        street_name: Wattle Street
        street_number: '188'
```
