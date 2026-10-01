# City of Melbourne

Support for schedules provided by [City of Melbourne](https://www.melbourne.vic.gov.au).

Source for City of Melbourne waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: melbourne_vic_gov_au
      args:
        lat: LAT
        lon: LON
```

### Configuration Variables

**lat**  
*(float) (required)*

**lon**  
*(float) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: melbourne_vic_gov_au
      args:
        lat: -37.78888528182715
        lon: 144.94807224053946
```

## How to get the source arguments

Pick the location of your property on the map. The collection zone of the City of Melbourne that contains it is used.
