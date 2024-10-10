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
        insee_code: "INSEE_CODE"
```

### Configuration Variables

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: dechets_gpseo_fr
      args:
        address: 11 rue Jean Moulin
        insee_code: "78362"
```

## How to find the insee code of your town

You should find it very easily on google.

## How to ensure your address is valid

Go on [GPSEO’s website](https://dechets.gpseo.fr/) and check how the autocomplete formats your address.
