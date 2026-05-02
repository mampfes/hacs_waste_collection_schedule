# SICTOM de Lons-le-Saunier

Support for schedules provided by [SICTOM de Lons-le-Saunier](https://sictom-lons-le-saunier.fr/) (Jura, France).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sictom_lons_le_saunier_fr
      args:
        commune: COMMUNE_SLUG
```

To find your commune slug:

1. Visit the [collection calendar](https://sictom-lons-le-saunier.fr/quand-passe-le-camion-benne.html) and search for your commune.
2. The slug is the commune name in lowercase, with spaces replaced by hyphens. For example, "Courbouzon" becomes `courbouzon`, and "Lons Le Saunier (Les Toupes)" becomes `lons-le-saunier-les-toupes`.

If the slug is not found, the source will suggest similar commune slugs from the API.

### Configuration Variables

**commune**
*(string) (required)*
The slug of your commune (e.g. `courbouzon`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sictom_lons_le_saunier_fr
      args:
        commune: "courbouzon"
```
