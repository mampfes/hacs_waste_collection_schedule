# Buchegg

Support for schedules provided by [Gemeinde Buchegg](https://www.buchegg-so.ch), Switzerland.

## How it works

This source fetches waste collection data from two providers:

| Waste type | Provider |
|------------|----------|
| Kehrichtabfuhr (household waste) | [buchegg-so.ch](https://www.buchegg-so.ch/abfalldaten) |
| Grüngutabfuhr (green waste) | [buchegg-so.ch](https://www.buchegg-so.ch/abfalldaten) |
| Altpapier (waste paper) | [localcities.ch](https://www.localcities.ch/de/entsorgung/buchegg/3385) |

Not all localities have Altpapier collection dates on localcities.ch. If unavailable, only Kehrichtabfuhr and Grüngutabfuhr are returned.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: buchegg_so_ch
      args:
        locality: LOCALITY
```

### Configuration Variables

**locality** *(string) (required)*: The name of your village (Ortsteil) within Gemeinde Buchegg.

Available values: `Aetigkofen`, `Aetingen`, `Bibern`, `Brittern`, `Brügglen`, `Gossliwil`, `Hessigkofen`, `Küttigkofen`, `Kyburg-Buchegg`, `Lüterswil-Gächliwil`, `Mühledorf`, `Tscheppach`

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: buchegg_so_ch
      args:
        ortschaft: "Aetingen"
```
