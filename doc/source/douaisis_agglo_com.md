# Douaisis Agglo

Support for schedules provided by [Douaisis Agglo](https://www.douaisis-agglo.com).

Source for the Douaisis Agglo (Nord) collection calendars, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: douaisis_agglo_com
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
    - name: douaisis_agglo_com
      args:
        commune: "Flines-lez-R\xE2ches"
```

## How to get the source arguments

Enter your commune as listed on https://www.douaisis-agglo.com/services/dechets/calendriers-de-collecte-de-votre-commune, for example `Flines-lez-Râches`. In Douai use the sector, for example `Douai - Dorignies`.
