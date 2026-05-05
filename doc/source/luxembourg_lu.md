# Luxembourg (All Communes)

Support for schedules provided by [data.public.lu](https://data.public.lu/fr/datasets/calendrier-des-dechets-collectes-par-commune/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: luxembourg_lu
      args:
        commune: COMMUNE
        # localite: LOCALITE
        # rue: RUE
```

### Configuration Variables

**commune**<br>
*(string) (required)* The commune name as found in the CSV.

**localite**<br>
*(string) (optional)* The locality name (required for communes that are subdivided by localities).

**rue**<br>
*(string) (optional)* The street name (required for localities that are subdivided by streets).

## How to get the arguments

Download/open the CSV from data.public.lu and copy the values from the columns **Commune**, **Localité** and **Rue** exactly (including accents).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: luxembourg_lu
      args:
        commune: Beaufort
```

