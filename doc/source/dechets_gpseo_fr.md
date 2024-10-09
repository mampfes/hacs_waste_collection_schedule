#dechets_gpseo_fr.md
# GPSEO - Communauté Urbaine

Support for schedules provided by [GPSEO - Communauté Urbaine](https://dechets.gpseo.fr/).

If collection data is available for the address provided, it will return waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: dechets_gpseo_fr
      args:
        address: "ADDRESS"
```

### Configuration Variables

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: dechets_gpseo_fr
      args:
        address: "11-rue-jean-moulin-mantes-la-ville"
```

## How to find your Valid Address

The only way to get your Valid URL is by typing your addres into [Tapez votre adresse](https://dechets.gpseo.fr/) and providng your address details with the hyphen code.
