# Grand Besançon Métropole

Support for schedules provided by [Grand Besançon Métropole](https://www.grandbesancon.fr).

Source for waste collection schedules in Grand Besançon Métropole, France.

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

**street**  
*(string) (required)*

**house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: grandbesancon_fr
      args:
        insee_code: '25014'
        street: Rue de Besancon
        house_number: '1'
```

## How to get the source arguments

Find your commune's INSEE code at https://www.insee.fr. Enter your street name as shown on the Grand Besançon waste calendar at https://data.grandbesancon.fr/opendata/dataset/joursDeCollecteDechets.
