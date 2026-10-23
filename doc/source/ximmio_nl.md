# Ximmio

Support for schedules provided by [Ximmio](https://www.ximmio.nl).

Source for Ximmio B.V. waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ximmio_nl
      args:
        company: COMPANY
        post_code: POST_CODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**company**  
*(string) (required)*

**post_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ximmio_nl
      args:
        company: acv
        post_code: 6721MH
        house_number: 1
```

## How to get the source arguments

Select your waste company, then enter the postcode and house number of your home address as on your company's waste calendar website.
