# MRC Matawinie (QC)

Support for schedules provided by [MRC Matawinie (QC)](https://gmrmatawinie.org).

Source script for gmrmatawinie.org

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gmrmatawinie_qc_ca
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
    - name: gmrmatawinie_qc_ca
      args:
        city_id: Saint-Alphonse-Rodriguez
```

## How to get the source arguments

Find your sector on the MRC Matawinie collection calendar at https://gmrmatawinie.org/calendriers-collectes/ and select it from the list.
