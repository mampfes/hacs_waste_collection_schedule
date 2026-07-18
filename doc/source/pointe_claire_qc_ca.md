# Pointe-Claire (QC)

Support for schedules provided by [Pointe-Claire (QC)](https://www.pointe-claire.ca).

Source for Pointe-Claire, Québec waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pointe_claire_qc_ca
      args:
        sector: SECTOR
```

### Configuration Variables

**sector**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pointe_claire_qc_ca
      args:
        sector: A
```

## How to get the source arguments

Find your collection sector on the City of Pointe-Claire website at https://www.pointe-claire.ca/en/residents/public-works/waste-management/
