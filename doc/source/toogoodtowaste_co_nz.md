# Hutt City Council

Support for schedules provided by [Hutt City Council](https://www.toogoodtowaste.co.nz/).

Source for Hutt City Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: toogoodtowaste_co_nz
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
    - name: toogoodtowaste_co_nz
      args:
        address: 493 Muritai Road EASTBOURNE
```

## How to get the source arguments

Enter your address exactly as the address finder on [toogoodtowaste.co.nz](https://www.toogoodtowaste.co.nz/) shows it, e.g. '30 Laings Road HUTT CENTRAL' (street in title case, suburb in capitals).
