# South Cambridgeshire District Council

Support for schedules provided by [South Cambridgeshire District Council](https://www.scambs.gov.uk/recycling-and-bins/find-your-household-bin-collection-day/), serving South Cambridgeshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: scambs_gov_uk
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
    - name: scambs_gov_uk
      args:
        post_code: "CB236GZ"
        number: "53"
```
