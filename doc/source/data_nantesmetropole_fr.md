# Nantes Métropole

Support for schedules provided by [Nantes Métropole](https://data.nantesmetropole.fr).

Source script for data.nantesmetropole.fr waste collection schedules (Nantes and a few bordering streets in neighbouring communes)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_nantesmetropole_fr
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
    - name: data_nantesmetropole_fr
      args:
        address: "16 Rue Abb\xE9 de l'Ep\xE9e, Nantes"
```

## How to get the source arguments

Enter your full street address including the house number and the city name (e.g. '16 Rue Abbé de l'Epée, Nantes').
