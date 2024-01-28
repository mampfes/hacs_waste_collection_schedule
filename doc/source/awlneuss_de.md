# Bürgerportal AWL Neuss

Support for schedules provided by [buergerportal.awl-neuss.de](https://buergerportal.awl-neuss.de).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awlneuss_de
      args:
        street_code: STREET_CODE
        building_number: BUILDING_NUMBER
```

### Configuration Variables

**street_code**  
*(string) (required)*

**building_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awlneuss_de
      args:
        street_code: 8650
        building_number: 13
```

## How to get the source arguments

To obtain the street parameter, a GET request must be made against the URL [https://buergerportal.awl-neuss.de/api/v1/calendar/townarea-streets](https://buergerportal.awl-neuss.de/api/v1/calendar/townarea-streets). The street must be searched for in the response. The value "strasseNummer" must be specified as a parameter `street_code`, as well as the house number as `building_number`
