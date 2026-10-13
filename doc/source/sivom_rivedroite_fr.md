# Sivom Rive Droite - Bassens

Support for schedules provided by [Sivom Rive Droite - Bassens](https://www.sivom-rivedroite.fr/).

Source for Sivom Rive Droite.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sivom_rivedroite_fr
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sivom_rivedroite_fr
      args:
        district: BASSENS 3
```

## How to get the source arguments

Enter your district exactly as named on the collection map at https://www.sivom-rivedroite.fr/ (e.g. 'BASSENS 3').
