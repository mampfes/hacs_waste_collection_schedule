# Christchurch City Council

Support for schedules provided by [Christchurch City Council](https://ccc.govt.nz/services/rubbish-and-recycling/collections).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ccc_govt_nz
      args:
        address: STREET_NUMBER_AND_STREET_NAME
```

### Configuration Variables

**address**  
*(string) (required)*

## Bin Names example - Garbage, Recycle & Organic

```yaml
waste_collection_schedule:
  sources:
    - name: ccc_govt_nz
      args:
        address: "53 Hereford Street"
```

## Bin Colours example - Red, Yellow & Green

```yaml
waste_collection_schedule:
  sources:
    - name: ccc_govt_nz
      args:
        address: "53 Hereford Street"
      customize:
          - type: Garbage
            alias: Red
          - type: Recycle
            alias: Yellow
          - type: Organic
            alias: Green
      calendar_title: "CCC Bins"
  separator: " & "
```
