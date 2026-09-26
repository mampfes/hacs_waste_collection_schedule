# Hamilton City Council

Support for schedules provided by [Hamilton City Council](https://www.fightthelandfill.co.nz/).

Source script for Hamilton City Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hcc_govt_nz
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
    - name: hcc_govt_nz
      args:
        address: 1 Hamilton Parade
```
