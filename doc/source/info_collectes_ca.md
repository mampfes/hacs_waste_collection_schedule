# MRC de Roussillon (QC)

Support for schedules provided by [MRC de Roussillon (QC)](https://info-collectes.ca/).

Source script for info-collectes.ca/

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

**municipality**  
*(string) (required)*

**sector**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: info_collectes_ca
      args:
        municipality: La Prairie
```

## How to get the source arguments

Your municipality in the MRC de Roussillon. Châteauguay also takes a sector: nord-ouest or est.
