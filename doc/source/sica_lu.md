# SICA

Support for municipalities being part of "**S**yndicat **I**ntercommunal pour l'hygiène publique du canton de **CA**pellen"

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sica_lu
      args:
        municipality: Steinfort
```

### Configuration Variables

The only configuration needed is the name of the municipality or town.

**municipality**
*(string) (required)*

Valid values is one of the following:

- Bertrange
- Capellen
- Garnich
- Habscht
- Holzem
- Kehlen
- Koerich
- Kopstal
- Mamer
- Steinfort

## Included collection types

- Bulky waste
- Clothing and Shoes
- Glass
- Organic waste
- Paper /Carton
- Residual waste
- Scrap and electrical appliances
- Hedges, Shrubs and Trees
- Valorlux - blue bag
