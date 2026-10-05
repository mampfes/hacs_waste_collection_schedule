# Winnipeg (MB)

Support for schedules provided by [Winnipeg (MB)](https://myutility.winnipeg.ca).

Source script for https://myutility.winnipeg.ca Use the same address as that works on the website under 'Find your collection day'

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: myutility_winnipeg_ca
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
    - name: myutility_winnipeg_ca
      args:
        address: 123 EASY ST
```

## How to get the source arguments

Use the same address that works on https://myutility.winnipeg.ca under 'Find your collection day'.
