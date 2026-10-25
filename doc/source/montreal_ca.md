# Montreal (QC)

Support for schedules provided by [Montreal (QC)](https://montreal.ca/info-collectes).

Source script for montreal.ca/info-collectes

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: montreal_ca
      args:
        sector: SECTOR
        recycling: RECYCLING
        bulky: BULKY
        food: FOOD
        green: GREEN
```

### Configuration Variables

**sector**  
*(string) (required)*

**recycling**  
*(string) (optional)*

**bulky**  
*(string) (optional)*

**food**  
*(string) (optional)*

**green**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: montreal_ca
      args:
        sector: LSL4
```

## How to get the source arguments

Download the Montreal GeoJSON file (https://donnees.montreal.ca/dataset/collecte-des-ordures-menageres), open it on https://geojson.io/ and find your sector on the map. Recycling, bulky items, food waste and greens use the waste sector unless you give a different one.
