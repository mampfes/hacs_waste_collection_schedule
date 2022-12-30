# Bracknell Forest Council

Support for schedules provided by [Bracknell Forest Council](https://selfservice.mybfc.bracknell-forest.gov.uk/w/webpage/waste-collection-days), serving Bracknell Forest, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: bracknell_forest_gov_uk
      args:
        post_code: Post Code
        house_number: House Number
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
        post_code: "RG42 2HB"
        house_number: "44"
```
