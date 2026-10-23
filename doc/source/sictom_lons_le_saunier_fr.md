# SICTOM de Lons-le-Saunier

Support for schedules provided by [SICTOM de Lons-le-Saunier](https://sictom-lons-le-saunier.fr).

Source for SICTOM de Lons-le-Saunier waste collection (Jura, France).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sictom_lons_le_saunier_fr
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
    - name: sictom_lons_le_saunier_fr
      args:
        commune: courbouzon
```

## How to get the source arguments

The slug of your commune (e.g. 'courbouzon'). Search on https://sictom-lons-le-saunier.fr/quand-passe-le-camion-benne.html to find your commune name, then convert to lowercase with hyphens.
