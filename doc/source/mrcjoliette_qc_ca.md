# MRC Joliette (QC)

Support for schedules provided by [MRC Joliette](https://mrcjoliette.qc.ca), Quebec, Canada.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mrcjoliette_qc_ca
      args:
        city_id: CITY_ID
```

### Configuration Variables

**city_id**
*(string) (required)*

The name of your city/sector as listed on the MRC Joliette collection map.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mrcjoliette_qc_ca
      args:
        city_id: Joliette - Mardi
```

## How to get the source arguments

Visit the [MRC Joliette collection map](https://mrcjoliette.qc.ca/gmr/carte-des-collectes/) and find your sector. Use the exact sector name from the list below as the `city_id` value:

- Crabtree
- Crabtree - Domaine
- Joliette - Mardi
- Joliette - Mercredi
- Joliette - Jeudi
- Joliette - Centre-ville
- Notre-Dame-de-Lourdes
- Notre-Dame-de-Lourdes - Domaine
- Notre-Dame-des-Prairies
- Notre-Dame-des-Prairies - Domaine
- Saint-Ambroise-de-Kildare
- Saint-Charles-Borromée - Mercredi
- Saint-Charles-Borromée - Jeudi
- Saint-Charles-Borromée - Domaine
- Sainte-Mélanie
- Saint-Paul
- Saint-Thomas
- Village Saint-Pierre
