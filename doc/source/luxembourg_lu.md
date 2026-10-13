# Luxembourg

Support for schedules provided by [Luxembourg](https://data.public.lu).

Source for Luxembourg waste collection using data.public.lu

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: luxembourg_lu
      args:
        commune: COMMUNE
        localite: LOCALITE
        rue: RUE
```

### Configuration Variables

**commune**  
*(string) (required)*

**localite**  
*(string) (optional)*

**rue**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: luxembourg_lu
      args:
        commune: Beaufort
```

## How to get the source arguments

Enter your commune as listed in the open data set on data.public.lu (the 'Commune' column, with accents). Communes that split their schedule also need the locality ('Localité') and, for some localities, the street ('Rue'). A missing or wrong value lists the valid ones.
