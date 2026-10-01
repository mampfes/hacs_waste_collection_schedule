# Toulouse Métropole

Support for schedules provided by [Toulouse Métropole](https://data.toulouse-metropole.fr).

Source pour la collecte des déchets de Toulouse Métropole (37 communes).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: toulouse_metropole_fr
      args:
        street_name: STREET_NAME
```

### Configuration Variables

**street_name**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: toulouse_metropole_fr
      args:
        street_name: Avenue Henri Guillaumet
```

## How to get the source arguments

Enter your street name exactly as it appears on the Toulouse Métropole open data portal. You can look it up at: https://data.toulouse-metropole.fr/explore/dataset/dechets-collecte-des-ordures-menageres/table/
