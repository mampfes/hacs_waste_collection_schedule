# Buchegg

Support for schedules provided by [Gemeinde Buchegg](https://www.buchegg-so.ch), Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: buchegg_so_ch
      args:
        ortschaft: ORTSCHAFT
```

### Configuration Variables

**ortschaft** *(string) (required)*: The name of your locality (Ortschaft) within Gemeinde Buchegg.

Available values: `Aetigkofen`, `Aetingen`, `Bibern`, `Brittern`, `Brügglen`, `Gossliwil`, `Hessigkofen`, `Küttigkofen`, `Kyburg-Buchegg`, `Lüterswil-Gächliwil`, `Mühledorf`, `Tscheppach`

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: buchegg_so_ch
      args:
        ortschaft: "Aetingen"
```
