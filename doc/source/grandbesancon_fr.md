# Grand Besançon Métropole

Support for waste collection schedules in [Grand Besançon Métropole](https://www.grandbesancon.fr) (68 communes), France, via the open data API.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: grandbesancon_fr
      args:
        insee_code: INSEE_CODE
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**insee_code**
*(string) (required)*

The 5-digit INSEE code of your commune (e.g. `25014` for Amagney, `25056` for Besançon).

**street**
*(string) (required)*

Your street name as shown in the Grand Besançon system.

**house_number**
*(string) (optional)*

Your house number. Helps filter results for large communes.

## How to get the source arguments

1. Find your commune's INSEE code at [insee.fr](https://www.insee.fr/fr/recherche/recherche-geographique).
2. Check your street name on the [Grand Besançon waste data page](https://data.grandbesancon.fr/opendata/dataset/joursDeCollecteDechets).

## Examples

### Amagney, Rue de Besancon 1

```yaml
waste_collection_schedule:
  sources:
    - name: grandbesancon_fr
      args:
        insee_code: "25014"
        street: "Rue de Besancon"
        house_number: "1"
```
