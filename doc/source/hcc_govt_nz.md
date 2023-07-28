# Hamilton City Council

Support for schedules provided by [Hamilton City Council](https://www.fightthelandfill.co.nz/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hcc_govt_nz
      args:
        address: STREET_NUMBER_AND_STREET_NAME
```

### Configuration Variables

**address**  
*(string) (required)*

## Bin Names example - Rubbish, Recycling

```yaml
waste_collection_schedule:
  sources:
    - name: hcc_govt_nz
      args:
        address: "1 Hamilton Parade"
```

## Bin Colours example - Red, Yellow

```yaml
waste_collection_schedule:
  sources:
    - name: hcc_govt_nz
      args:
        address: "1 Hamilton Parade"
      customize:
          - type: Rubbish
            alias: Red
          - type: Recycling
            alias: Yellow
      calendar_title: "HCC Bins"
  separator: " & "
```
