# MRC Joliette (QC)

Support for schedules provided by [MRC Joliette (QC)](https://mrcjoliette.qc.ca).

Source script for mrcjoliette.qc.ca

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

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mrcjoliette_qc_ca
      args:
        city_id: Joliette - Mardi
```

## How to get the source arguments

Find your sector on the MRC Joliette collection map at https://mrcjoliette.qc.ca/gmr/carte-des-collectes/ and pick it from the list.
