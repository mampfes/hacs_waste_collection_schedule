# Montreal

Waste collection schedules provided by [Info Collecte Montreal](https://montreal.ca/info-collectes/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: montreal_ca
      args:
        sector: SECTOR
```

### Configuration Variables

**sector**
*(string) (required)*

**How do I find my sector?**

- Download on your computer a [Montreal GeoJSON file](https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/5f3fb372-64e8-45f2-a406-f1614930305c/download/collecte-des-ordures-menageres.geojson)
- Visit https://geojson.io/
- Click on *Open* and select the Montreal GeoJSON file
- Find your sector on the map

![Alt text](../../images/montreal_ca_helper.png)



## Example

```yaml
waste_collection_schedule:
  sources:
    - name: montreal_ca
      args:
        sector: MHM_41-1
```
