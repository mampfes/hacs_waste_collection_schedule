# Métropole de Lyon

Support for schedules provided by [data.grandlyon.com](https://data.grandlyon.com), serving 59 communes in the Lyon metropolitan area.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_grandlyon_com
      args:
        address: "1 place Roger Salengro, Oullins"
```

### Configuration Variables

**address** *(string) (required)*

Your full street address including the city name.

### Examples

```yaml
waste_collection_schedule:
  sources:
    - name: data_grandlyon_com
      args:
        address: "208 rue Garibaldi, Lyon"
```
