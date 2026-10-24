# Val ès Dunes

Support for schedules provided by [Val ès Dunes](https://www.valesdunes.fr).

Source for the Val ès Dunes (Calvados) collection calendars, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: valesdunes_fr
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
    - name: valesdunes_fr
      args:
        commune: Bellengreville
```

## How to get the source arguments

Enter your commune as listed on https://www.valesdunes.fr/calendriers-de-collecte/, for example `Bellengreville`.
