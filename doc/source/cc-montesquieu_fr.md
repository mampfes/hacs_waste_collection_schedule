# Communauté de Communes de Montesquieu

Support for schedules provided by [Communauté de Communes de Montesquieu](https://www.cc-montesquieu.fr/).

Source for the waste collection of the Communauté de Communes de Montesquieu (Gironde).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cc-montesquieu_fr
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
    - name: cc-montesquieu_fr
      args:
        commune: Ayguemorte-les-Graves
```

## How to get the source arguments

Enter your commune as it is listed on https://www.cc-montesquieu.fr/vivre/dechets/collectes-des-dechets (for example 'La Brède' or 'Saint-Médard-d'Eyrans').
