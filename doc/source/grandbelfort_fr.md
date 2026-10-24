# Grand Belfort

Support for schedules provided by [Grand Belfort](https://www.grandbelfort.fr).

Source for the Grand Belfort (Territoire de Belfort) collection calendars, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: grandbelfort_fr
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
    - name: grandbelfort_fr
      args:
        commune: Cravanche
```

## How to get the source arguments

Enter your commune as listed on https://www.grandbelfort.fr/prevention-et-valorisation-des-dechets/calendriers-de-collecte.html, for example `Cravanche`. In Belfort use `Belfort - ` followed by your sector, for example `Belfort - La Pépinière`.
