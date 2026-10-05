# Hume City Council

Support for schedules provided by [Hume City Council](https://hume.vic.gov.au).

Source for hume.vic.gov.au Waste Collection Services

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hume_vic_gov_au
      args:
        address: ADDRESS
        predict: PREDICT
```

### Configuration Variables

**address**  
*(string) (required)*

**predict**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hume_vic_gov_au
      args:
        address: 19 Potter Street Craigieburn 3064
        predict: true
```

## How to get the source arguments

Enter your address as it appears on the Hume City Council 'Know my bin day' page. Council only publishes the next collection date for each bin. Turn on 'predict' to project the following four weeks from the collection frequency the council states.
