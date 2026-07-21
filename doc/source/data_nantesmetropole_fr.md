# Nantes Métropole

Support for schedules provided by [data.nantesmetropole.fr](https://data.nantesmetropole.fr), the open data portal of Nantes Métropole, mainly covering the city of Nantes (a handful of streets bordering Saint-Herblain, Orvault, Bouguenais and Saint-Sébastien-sur-Loire may also be found).

The dataset only lists the fixed weekday(s) on which "bacs bleus" (residual household waste) and "bacs jaunes" (recyclables) are collected for each street, not a full calendar with holiday exceptions. Streets served by public drop-off containers ("colonnes") instead of door-to-door collection will not produce any entries for that waste stream.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_nantesmetropole_fr
      args:
        address: "16 Rue Abbé de l'Epée, Nantes"
```

### Configuration Variables

**address** *(string) (required)*

Your full street address, including the house number and the city name.

### Examples

```yaml
waste_collection_schedule:
  sources:
    - name: data_nantesmetropole_fr
      args:
        address: "89 Rue du Port Boyer, Nantes"
```
