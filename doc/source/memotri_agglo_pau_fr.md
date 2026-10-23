# Mémotri - Agglomération Pau Béarn Pyrénées

Support for schedules provided by [Mémotri - Agglomération Pau Béarn Pyrénées](https://memotri.agglo-pau.fr/).

Source script for memotri.agglo-pau.fr

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

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: memotri_agglo_pau_fr
      args:
        address: 39 avenue larribau 64000 Pau
```

## How to get the source arguments

Enter your full address as you would on the memotri.agglo-pau.fr website, including street number, street name, postal code, and city.
