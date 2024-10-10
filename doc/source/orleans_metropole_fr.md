#orleans_metropole_fr.md
# Orléans Métropole

Support for schedules provided by [Orléans Métropole](https://triermondechet.orleans-metropole.fr/).

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
    - name: orleans_metropole_fr
      args:
        address: 13 rue de la Commanderie
        insee_code: "45034"
```

## How to find the insee code of your town

You should find it very easily on google.

## How to ensure your address is valid

Go on [Orléans Métropole’s website](https://triermondechet.orleans-metropole.fr/) and check how the autocomplete formats your address.
