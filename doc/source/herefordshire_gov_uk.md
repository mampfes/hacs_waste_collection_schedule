# Herefordshire County Council

Support for schedules provided by [Herefordshire County
Council](https://www.herefordshire.gov.uk/environmental-protection/waste-management/refuse-household-bin-collection),
serving Herefordshire (UK).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: herefordshire_gov_uk
      args:
        post_code: POST_CODE
        number: NUMBER

```

### Configuration Variables

**POST_CODE**  
*(string) (required)*

**NUMBER**  
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: canterbury_gov_uk
      args:
        post_code: "hr49js"
        number: "1"
```
