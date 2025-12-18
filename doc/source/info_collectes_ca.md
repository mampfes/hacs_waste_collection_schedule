# info-collectes - waste schedule for MRC de Roussillon (QC, Canada)

Waste collection schedules provided by [Info Collectes MRC de Roussillon](https://info-collectes.ca/).

Including the following communities:

  - Candiac
  - Châteauguay
  - Delson
  - La Prairie
  - Léry
  - Mercier
  - Saint-Constant
  - Saint-Isidore
  - Saint-Mathieu
  - Saint-Philippe
  - Sainte-Catherine


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: info_collectes_ca
      args:
        municipality: MUNICIPALITY
        sector: SECTOR
```

### Configuration Variables

* **municipality** *(string) (required)*: Municipality in MRC de Roussillon, case insensitive
* **sector** *(string) (optional)*: For Châteauguay only, valid sectors are: nord-ouest, est

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: info_collectes_ca
      args:
        municipality: La Prairie
```