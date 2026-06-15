# Toulouse Métropole

Support for household waste collection schedules in [Toulouse Métropole](https://www.toulouse-metropole.fr/), based on the [open data portal](https://data.toulouse-metropole.fr/).

The dataset covers 37 municipalities in Haute-Garonne (31), France.

## Configuration via `configuration.yaml`

```yaml
waste_collection_schedule:
    sources:
    - name: toulouse_metropole_fr
      args:
        street_name: STREET_NAME
```

### Configuration Variables

**street_name**  
*(String) (required)*

Name of your street, exactly as it appears in the open data portal (e.g. `Avenue Henri Guillaumet`).

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: toulouse_metropole_fr
      args:
        street_name: Avenue Henri Guillaumet
```

```yaml
waste_collection_schedule:
    sources:
    - name: toulouse_metropole_fr
      args:
        street_name: Rue de la Paix
```

## How to get the source arguments

Visit the dataset page at [data.toulouse-metropole.fr](https://data.toulouse-metropole.fr/explore/dataset/dechets-collecte-des-ordures-menageres/table/) and look up your street. The `libelle_voie` column gives the value to use for `street_name`.
