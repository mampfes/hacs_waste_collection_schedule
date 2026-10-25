# Ville de Blainville

Support for schedules provided by [Ville de Blainville](https://blainville.ca).

Source for the Ville de Blainville (Québec) residential collection calendar.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: blainville_ca
      args:
        secteur: SECTEUR
```

### Configuration Variables

**secteur**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: blainville_ca
      args:
        secteur: Nord
```

## How to get the source arguments

Choose your sector (Nord or Sud) as shown on the map of the collection calendar on https://blainville.ca/services/environnement-et-voirie/collectes-et-matieres-residuelles: the north sector is collected on Wednesdays, the south sector on Tuesdays. The calendar covers homes and buildings of nine units or fewer.
