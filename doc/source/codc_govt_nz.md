# Central Otago District Council

Support for schedules provided by [Central Otago District Council](https://www.codc.govt.nz/).

Source for Central Otago District Council Rubbish & Recycling collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: codc_govt_nz
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
    - name: codc_govt_nz
      args:
        address: 5 Campbell Street Alexandra
```

## How to get the source arguments

Enter the full street address as displayed in the CODC Bin App, e.g. '5 Campbell Street Alexandra'.
