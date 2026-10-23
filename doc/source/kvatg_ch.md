# KVA Thurgau

Support for schedules provided by [KVA Thurgau](https://www.kvatg.ch).

Source for KVA Thurgau (Kehrichtverwertungsanlage Thurgau) waste collection, covering the municipalities of the canton of Thurgau and neighbouring communities, Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kvatg_ch
      args:
        community: COMMUNITY
        zone: ZONE
        kehricht_zone: KEHRICHT_ZONE
```

### Configuration Variables

**community**  
*(string) (required)*

**zone**  
*(string) (optional)*

**kehricht_zone**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kvatg_ch
      args:
        community: Kreuzlingen
```

## How to get the source arguments

Find your community on https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/ and enter its name. If your community's disposal plan splits a collection by zone (e.g. the green waste districts in Kreuzlingen or the collection areas in Frauenfeld), you can optionally enter the zone name as printed in the plan; an invalid value shows a list of the valid names. Only for Kreuzlingen, kehricht_zone selects the household-waste zone of the city's own zone plan ('Süd & Tägerwilen', 'Nord und Ost' or 'Zentrum'); leave it empty to get all three.
