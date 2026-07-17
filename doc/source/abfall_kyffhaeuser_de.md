# Abfallwirtschaft Kyffhäuserkreis

Support for waste collection schedules provided by [Abfallwirtschaft Kyffhäuserkreis](https://abfall-kyffhaeuser.de/), covering towns and villages within the Kyffhäuserkreis district, Thuringia, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_kyffhaeuser_de
      args:
        city: Ebeleben
```

### Configuration Variables

**city**
*(string) (required)*

The place name as shown in the "Ort" filter on the [collection calendar](https://abfall-kyffhaeuser.de/kalender/), e.g. `Ebeleben`.

Larger towns (Bad Frankenhausen, Sondershausen, Artern) are split into several collection tours, e.g. `Bad Frankenhausen - Tour 1`, `Bad Frankenhausen - Tour 2`, `Bad Frankenhausen - Tour 3`. Check your waste collection notice / bin sticker, or ask Abfallwirtschaft Kyffhäuserkreis, to find out which tour serves your street.

If you enter an unknown or ambiguous place name, the resulting error message lists all valid place names (or, for towns with multiple tours, just the matching tours) so you can pick the correct one.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_kyffhaeuser_de
      args:
        city: Bad Frankenhausen - Tour 1
```

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_kyffhaeuser_de
      args:
        city: Sondershausen - Tour 3
```

## How to get the source argument

Visit [https://abfall-kyffhaeuser.de/kalender/](https://abfall-kyffhaeuser.de/kalender/), open the "Ort" filter dropdown and copy the exact place name shown there.
