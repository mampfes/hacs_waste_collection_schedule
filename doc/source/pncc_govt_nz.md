# Palmerston North City Council

Support for schedules provided by [Palmerston North City Council](https://www.pncc.govt.nz/Services/Rubbish-and-recycling/Palmy-Collections/Rubbish-and-recycling-days), New Zealand.

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

Your street address, including the city name.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pncc_govt_nz
      args:
        address: 8 Swansea Street Palmerston North
```

## How to get the source arguments

1. Visit the [Rubbish and recycling days](https://www.pncc.govt.nz/Services/Rubbish-and-recycling/Palmy-Collections/Rubbish-and-recycling-days) page.
2. Search for your address.
3. Use the address as shown in the search result, for example `8 Swansea Street Palmerston North`.
