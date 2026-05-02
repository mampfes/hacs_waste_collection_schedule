# Mémotri - Agglomération Pau Béarn Pyrénées

Support for schedules provided by [Mémotri - Agglomération Pau Béarn Pyrénées](https://memotri.agglo-pau.fr/), serving the Pau agglomeration area in France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: memotri_agglo_pau_fr
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Full address including street number, street name, postal code, and city.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: memotri_agglo_pau_fr
      args:
        address: "39 avenue larribau 64000 Pau"
```

## How to get the source argument

Visit [https://memotri.agglo-pau.fr/](https://memotri.agglo-pau.fr/) and enter your address in the search field. Use the same address format in the configuration.
