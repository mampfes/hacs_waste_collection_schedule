# Cambridge City Council

Support for schedules provided by [Cambridge City Council](https://www.cambridge.gov.uk/check-when-your-bin-will-be-emptied), serving Cambridge (UK) and part of Cambridgeshire.

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

**POST_CODE**  
*(string) (required)*

**NUMBER**  
*(string) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: cambridge_gov_uk
      args:
        post_code: "CB13JD"
        number: "37"
```
