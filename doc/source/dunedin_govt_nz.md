# Dunedin District Council

Support for schedules provided by [Dunedin District Council](https://www.dunedin.govt.nz/).

Source for Dunedin District Council Rubbish & Recycling collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dunedin_govt_nz
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
    - name: dunedin_govt_nz
      args:
        address: 5 Bennett Road Ocean View
```

## How to get the source arguments

Enter the full street address as displayed in the DCC Kerbside Collection app, e.g. '5 Bennett Road Ocean View'.
