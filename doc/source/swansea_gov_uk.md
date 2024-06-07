# Swansea Council

Support for schedules provided by [Swansea Council](https://swansea.gov.uk/), UK.

If collection data is available for the address provided, it will return household and recycling waste collection dates.


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: swansea_gov_uk
      args:
        street_name: STREET_NAME
        post_code: POST_CODE
```

### Configuration Variables

**street_name** 

_(string) (required)_

Any part of the road/street name

**post_code**

_(string) (required)_

Full postcode of the property

## Example:

```yaml
waste_collection_schedule:
    sources:
    - name: swansea_gov_uk
      args:
        street_name: "Oystermouth Road"
        post_code: "SA1 3SN"
```

## How to verify that your address works

Visit [swansea.gov.uk/recyclingsearch](https://swansea.gov.uk/recyclingsearch) and search for your street name and postcode.
