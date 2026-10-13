# Métropole de Lyon

Support for schedules provided by [Métropole de Lyon](https://data.grandlyon.com).

Source script for data.grandlyon.com waste collection schedules

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_grandlyon_com
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
    - name: data_grandlyon_com
      args:
        address: 1 place Roger Salengro, Oullins
```

## How to get the source arguments

Enter your street address including the city name (e.g. '1 place Roger Salengro, Oullins').
