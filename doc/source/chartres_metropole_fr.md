# Chartres Métropole

Support for schedules provided by [Chartres Métropole](https://www.chartres-metropole.fr/dechets/collectes).

Source for Chartres Métropole, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: chartres_metropole_fr
      args:
        commune: COMMUNE
        secteur: SECTEUR
```

### Configuration Variables

**commune**  
*(string) (required)*

**secteur**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: chartres_metropole_fr
      args:
        commune: "L\xE8ves"
```

## How to get the source arguments

Visit https://www.chartres-metropole.fr/dechets/collectes, find your commune and use the name as displayed there. Set 'secteur' only if you know you are on the bin ('bacs') or bag ('sacs') round; leave it empty to receive both.
