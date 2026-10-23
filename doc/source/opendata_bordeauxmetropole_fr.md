# Bordeaux Métropole

Support for schedules provided by [Bordeaux Métropole](https://opendata.bordeaux-metropole.fr/).

Source script for opendata.bordeaux-metropole.fr

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: opendata_bordeauxmetropole_fr
      args:
        address: ADDRESS
        city: CITY
```

### Configuration Variables

**address**  
*(string) (required)*

**city**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: opendata_bordeauxmetropole_fr
      args:
        address: 20 Cr Pasteur
        city: Bordeaux
```

## How to get the source arguments

Choose your commune and enter your street address without the city (e.g. '20 Cours Pasteur'). The collection days are those of the zone the address lies in.
