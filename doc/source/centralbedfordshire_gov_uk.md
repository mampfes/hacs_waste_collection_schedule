# Central Bedfordshire Council

Support for schedules provided by [Central Bedfordshire Council](https://www.centralbedfordshire.gov.uk/info/163/bins_and_waste_collections_-_check_bin_collection_days/), serving Central Bedfordshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: centralbedfordshire_gov_uk
      args:
        post_code: POST_CODE
        house_name: HOUSE_NAME
        version: 1

```

### Configuration Variables

**POST_CODE**  
*(string) (required)*

**HOUSE_NAME**  
*(string) (required)*

This must exactly match your house name that the search on [Central Bedfordshire Council's website](https://www.centralbedfordshire.gov.uk/info/163/bins_and_waste_collections_-_check_bin_collection_days) returns for your given postcode EXCLUDING the comma and postcode

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: centralbedfordshire_gov_uk
      args:
        post_code: "SG156YF"
        house_name: "10 Old School Walk"
```
