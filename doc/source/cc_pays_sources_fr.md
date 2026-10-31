# Communauté de Communes du Pays des Sources

Support for schedules provided by [Communauté de Communes du Pays des Sources](https://www.cc-pays-sources.fr).

Source for the Pays des Sources (Oise) collection calendars, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cc_pays_sources_fr
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
    - name: cc_pays_sources_fr
      args:
        commune: Ressons-sur-Matz
```

## How to get the source arguments

Enter your commune as listed in the drop-down on https://www.cc-pays-sources.fr/environnement/gestion-des-dechets/votre-calendrier-de-tri/, for example `Ressons-sur-Matz`.
