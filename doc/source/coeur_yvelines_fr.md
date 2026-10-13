# Coeur d'Yvelines

Support for schedules provided by [Coeur d'Yvelines](https://www.coeur-yvelines.fr/).

Source script for coeur-yvelines.fr

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: coeur_yvelines_fr
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
    - name: coeur_yvelines_fr
      args:
        commune: Auteuil-le-Roi
```
