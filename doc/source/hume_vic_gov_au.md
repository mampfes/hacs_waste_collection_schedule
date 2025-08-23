# Hume City Council

Waste collection schedules provided by [Hume City Council](https://www.hume.vic.gov.au).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hume_vic_gov_au
      args:
        post_code: POST_CODE
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**post_code**  
*(string) (required)*

**suburb**  
*(string) (required)*

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hume_vic_gov_au
      args:
        post_code: 3064
        suburb: Kalkallo
        street_name: Toyon Road
        street_number: 33
```
## How to get the source arguments

Visit the [Hume City Council - Know my bin day](https://www.hume.vic.gov.au/Residents/Waste/Know-my-bin-day) page, and search for your address. The street address arguments used to configure hacs_waste_collection_schedule should exactly match the street address shown in the autocomplete result.

# Similarities with other sources

Hume City Council previously used a different API, but now uses the same as Blacktown City Council (NSW), Cambelltown City Council (NSW), and tbe City of Ryde (NSW). I was able to copy the code with minimal modification to get Hume City Council to work.