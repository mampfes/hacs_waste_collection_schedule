# Bürgerportal AWL Neuss

Support for schedules provided by [buergerportal.awl-neuss.de](https://buergerportal.awl-neuss.de).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awlneuss_de
      args:
        street_name: STREET_NAME
        street_code: STREET_CODE
        building_number: BUILDING_NUMBER
```

### Configuration Variables

**street_name**   
*(string) (required)* 

**building_number**  
*(int) (required)*

**street_code**  
*(int) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awlneuss_de
      args:
        street_name: "Theodor-Heuss-Platz"
        building_number: 13
```
```yaml
waste_collection_schedule:
  sources:
    - name: awlneuss_de
      args:
        street_code: 8650
        building_number: 13
```

## How to get the source arguments

### use the parameter street_name
Please go to the website [https://buergerportal.awl-neuss.de/calendar]([https://buergerportal.awl-neuss.de/calendar) and search for your street and enter it exactly as it appears in the textbox.

### use the parameter street_code
To obtain the street parameter, a GET request must be made against the URL [https://buergerportal.awl-neuss.de/api/v1/calendar/townarea-streets](https://buergerportal.awl-neuss.de/api/v1/calendar/townarea-streets). The street must be searched for in the response. The value "strasseNummer" must be specified as a parameter `street_code`, as well as the house number as `building_number`. If the `street_code` parameter is set the parameter `street` is optional.
