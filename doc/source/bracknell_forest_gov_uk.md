# Bracknell Forest Council

Support for schedules provided by [Bracknell Forest Council](https://selfservice.mybfc.bracknell-forest.gov.uk).

Bracknell Forest Council, UK - Waste Collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bracknell_forest_gov_uk
      args:
        post_code: POST_CODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**post_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bracknell_forest_gov_uk
      args:
        house_number: '44'
        post_code: RG42 2HB
```
