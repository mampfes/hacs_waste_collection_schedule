# OpenData Bordeaux Métropole — provider for waste management schedules

Support for schedules provided by [Bordeaux Métropole](https://opendata.bordeaux-metropole.fr/).

They operate the schedules of at least these cities:

- Bordeaux
- Mérignac
- Gradignan
- Talence
- Saint-Médard-en-Jalles
- Villenave-d'Ornon
- Bruges
- Bègles
- Le Bouscat
- Pessac
- Ambarès-et-Lagrave
- Ambès
- Blanquefort
- Eysines
- Le Haillan
- Le Taillan-Médoc
- Martignas-sur-Jalle
- Parempuyre
- Saint-Aubin-de-Médoc
- Saint-Louis-de-Montferrand
- Saint-Vincent-de-Paul

You only have to provide your address.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: opendata_bordeauxmetropole_fr
      args:
        address: "ADDRESS"
        city: "CITY_NAME"
```

### Configuration Variables

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: opendata_bordeauxmetropole_fr
      args:
        address: "11 rue Jean Moulin"
        city: "Bordeaux"
```

## How to ensure your address is valid

Go on [OpenData BordeauxMetropole’s website](https://opendata.bordeaux-metropole.fr/explore/dataset/en_frcol_s/map/?disjunctive.jour_col&basemap=jawg.streets) and try to search your address.
