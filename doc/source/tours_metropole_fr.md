#tours_metropole_fr.md
# Tours Métropole

Support for schedules provided by [Tours Métropole](https://www.tours-metropole.fr/mes-poubelles-connaitre-les-jours-de-collecte-et-sinformer-sur-le-tri).

If collection data is available for the address provided, it will return waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: dechets_gpseo_fr
      args:
        address: "ADDRESS"
        insee_code: "INSEE_CODE"
```

### Configuration Variables

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: tours_metropole_fr
      args:
        address: 3 Rue de Miré
        insee_code: "37018"
```

## How to find the insee code of your town

You should find it very easily on google.

## How to ensure your address is valid

Go on [Tours Métropole’s website](https://www.tours-metropole.fr/mes-poubelles-connaitre-les-jours-de-collecte-et-sinformer-sur-le-tri) and check how the autocomplete formats your address.
