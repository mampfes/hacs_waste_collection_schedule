# Golfe du Morbihan - Vannes agglomération

Support for schedules provided by [Golfe du Morbihan - Vannes agglomération](https://www.golfedumorbihan-vannesagglomeration.bzh).

Source for the Golfe du Morbihan - Vannes agglomération collection calendars, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gmvagglo_bzh
      args:
        commune: COMMUNE
```

### Configuration Variables

**commune**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmvagglo_bzh
      args:
        commune: Ploeren
```

## How to get the source arguments

Enter your commune (or sector) as listed under 'Calendriers de collecte' on https://www.golfedumorbihan-vannesagglomeration.bzh/mon-quotidien/dechets/collecte/, for example `Ploeren` or `Vannes secteur 3`.
