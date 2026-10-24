# SIVOM du Louhannais

Support for schedules provided by [SIVOM du Louhannais](https://sivom-louhannais.fr).

Source for the SIVOM du Louhannais (Saône-et-Loire) collection calendars, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sivom_louhannais_fr
      args:
        jour: JOUR
```

### Configuration Variables

**jour**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sivom_louhannais_fr
      args:
        jour: Vendredi
```

## How to get the source arguments

Choose your commune's collection weekday as listed on https://sivom-louhannais.fr/collecte-des-omr/les-calendriers-de-collecte.html (for example Beaurepaire-en-Bresse: `Vendredi`).
