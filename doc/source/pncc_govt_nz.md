# Palmerston North City Council

Support for schedules provided by [Palmerston North City Council](https://www.pncc.govt.nz/Services/Rubbish-and-recycling/Palmy-Collections/Rubbish-and-recycling-days).

Source for Palmerston North City Council rubbish and recycling collections.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pncc_govt_nz
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
    - name: pncc_govt_nz
      args:
        address: 8 Swansea Street Palmerston North
```

## How to get the source arguments

Enter your street address as it appears in the search on the Palmerston North City Council 'Rubbish and recycling days' page, for example '8 Swansea Street Palmerston North'.
