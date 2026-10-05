# Abfallwirtschaft Kyffhäuserkreis

Support for schedules provided by [Abfallwirtschaft Kyffhäuserkreis](https://abfall-kyffhaeuser.de).

Source for Abfallwirtschaft Kyffhäuserkreis, covering waste collection schedules for towns and villages within the Kyffhäuserkreis district, Thuringia, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_kyffhaeuser_de
      args:
        city: CITY
```

### Configuration Variables

**city**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_kyffhaeuser_de
      args:
        city: Ebeleben
```

## How to get the source arguments

Visit https://abfall-kyffhaeuser.de/kalender/, open the 'Ort' filter and use the exact place name shown there as the 'city' argument. Larger towns (Bad Frankenhausen, Sondershausen, Artern) are split into several collection tours ('Tour 1', 'Tour 2', ...) - check your bin / waste collection notice or ask the Kyffhäuserkreis waste department which tour serves your street. If you enter an unknown or ambiguous name, the resulting error message will list the valid place names.
