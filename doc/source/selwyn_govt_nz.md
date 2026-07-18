# Selwyn District Council

Support for schedules provided by [Selwyn District Council](https://www.selwyn.govt.nz/).

Source for Selwyn District Council kerbside waste collection, New Zealand.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: selwyn_govt_nz
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
    - name: selwyn_govt_nz
      args:
        address: 30 Tennyson Street Rolleston
```

## How to get the source arguments

Enter your address exactly as it appears in the address search on Selwyn District Council's collection days and routes page, e.g. '30 Tennyson Street Rolleston'.
