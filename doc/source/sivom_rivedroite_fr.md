# Sivom Rive Droite

Support for schedules provided by [Sivom Rive Droite](https://www.sivom-rivedroite.fr/), serving Bassens, France.

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
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: sivom_rivedroite_fr
      args:
        district: BASSENS 3
```

## How to get the source argument

Visit [https://www.sivom-rivedroite.fr/media/2986](https://www.sivom-rivedroite.fr/media/2986) and look for your district on the map district should match the name of the district name when clicked on your district on the map.

