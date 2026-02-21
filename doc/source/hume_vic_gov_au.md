# Hume City Council

Waste collection schedules provided by [Hume City Council](https://www.hume.vic.gov.au).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hume_vic_gov_au
      args:
        address: ADDRESS # FORMATTING MUST BE EXACT, PLEASE SEE BELOW
        predict: PREDICT
```

### Configuration Variables

**address**  
*(string) (required)*

**predict**  
*(bool) (optional, default=False)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hume_vic_gov_au
      args:
        address: "19 Potter Street Craigieburn 3064"
        predict: True
```

## How to get the correct address

Visit the [Hume City Council - Know my bin day](https://www.hume.vic.gov.au/Residents/Waste/Know-my-bin-day) page, and search for your address. The street address used to configure hacs_waste_collection_schedule should exactly match the street address shown in the autocomplete result.

## Prediction of future collections

Extrapolation of future collections can be returned using the PREDICT boolean. If enabled, 4 weeks worth of collections will be returned based on the known schedule. Only the first value of each is returned from the Council website, the rest are predicted. Non collection days or holidays are not taken into account.

## Similarities with other sources

Hume City Council previously used a different API, but now uses the same as Blacktown City Council (NSW), Cambelltown City Council (NSW), and the City of Ryde (NSW). This source does not split the postcode, suburb, street name and street number into separate arguments, so that backwards compatibility is maintained with the old arg format.
