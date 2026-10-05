# Agglomération de La Rochelle

Support for schedules provided by [Agglomération de La Rochelle](https://www.agglo-larochelle.fr).

Source for waste collection in La Rochelle agglomeration.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: larochelle_fr
      args:
        sector: SECTOR
```

### Configuration Variables

**sector**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: larochelle_fr
      args:
        sector: La Rochelle Secteur A
```

## How to get the source arguments

Select your municipality, or for La Rochelle, Châtelaillon-Plage and the sectors L to O, your collection sector. Find it on the map: https://opendata.agglo-larochelle.fr/visualisation/map/?id=dechet_-_prochaines_dates_de_collecte
