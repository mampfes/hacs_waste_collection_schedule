# Allerdale Borough Council

Support for schedules provided by [Allerdale Borough Council](https://www.allerdale.gov.uk/en/waste-recycling/), serving the Allerdale district, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: allerdale_gov_uk
      args:
        address_postcode: POST_CODE
        address_name_number: HOUSE_NAME_NUMBER
```

### Configuration Variables
If you have a house name, or both a house name and house number, determine which is best to use manually at [Allerdale Borough Council](https://www.allerdale.gov.uk/en/waste-recycling/).


**ADDRESS_POSTCODE**  
*(string) (required)*

**ADDRESS_NAME_NUMBER**  
*(string) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: allerdale_gov_uk
      args:
        address_postcode: "CA12 4HU"
        address_name_number: "11"
```
