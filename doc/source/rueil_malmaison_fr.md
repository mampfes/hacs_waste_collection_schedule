# Rueil-Malmaison

Support for schedules provided by [Rueil-Malmaison](https://www.rueil-malmaison.fr).

Source for waste collection schedule in Rueil-Malmaison, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rueil_malmaison_fr
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
    - name: rueil_malmaison_fr
      args:
        lat: 48.8768
        lon: 2.1875
```

## How to get the source arguments

Pick your address on the map. The collection zones come from the Hauts-de-Seine open data portal (opendata.hauts-de-seine.fr).
