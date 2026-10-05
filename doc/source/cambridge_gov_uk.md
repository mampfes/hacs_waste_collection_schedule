# Cambridge City Council (Deprecated)

Support for schedules provided by [Cambridge City Council (Deprecated)](https://cambridge.gov.uk).

Source for cambridge.gov.uk services for Cambridge and part of Cambridgeshire

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cambridge_gov_uk
      args:
        post_code: POST_CODE
        number: NUMBER
```

### Configuration Variables

**post_code**  
*(string) (required)*

**number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cambridge_gov_uk
      args:
        post_code: CB13JD
        number: 37
```
