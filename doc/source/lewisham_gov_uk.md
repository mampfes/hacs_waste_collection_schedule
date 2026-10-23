# London Borough of Lewisham

Support for schedules provided by [London Borough of Lewisham](https://lewisham.gov.uk).

Source for services from the London Borough of Lewisham

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lewisham_gov_uk
      args:
        post_code: POST_CODE
        number: NUMBER
        name: NAME
        uprn: UPRN
```

### Configuration Variables

**post_code**  
*(string) (optional)*

**number**  
*(string) (optional)*

**name**  
*(string) (optional)*

**uprn**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lewisham_gov_uk
      args:
        post_code: SE41LR
        number: 4
```
