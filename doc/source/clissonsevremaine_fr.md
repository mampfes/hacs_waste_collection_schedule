# Clisson Sèvre et Maine Agglo

Support for schedules provided by [Clisson Sèvre et Maine Agglo](https://environnement.clissonsevremaine.fr).

Source for Clisson Sèvre et Maine Agglo, the inter-municipal authority responsible for waste collection in 18 municipalities of the Loire-Atlantique department, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: clissonsevremaine_fr
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
    - name: clissonsevremaine_fr
      args:
        commune: Gorges
```

## How to get the source arguments

Open https://environnement.clissonsevremaine.fr/dechets/collecte-des-dechets/calendrier-des-collectes and pick your municipality in the drop-down menu. Use the wording shown there. Some municipalities are split into several collection zones; the maps at the end of the downloadable PDF calendars tell you which zone your street belongs to.
