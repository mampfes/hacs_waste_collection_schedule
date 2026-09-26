# South Cambridgeshire District Council (Deprecated)

Support for schedules provided by [South Cambridgeshire District Council (Deprecated)](https://scambs.gov.uk).

Source for scambs.gov.uk services for South Cambridgeshire District Council

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

**post_code**  
*(string) (required)*

**number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: scambs_gov_uk
      args:
        post_code: CB236GZ
        number: 53
```
