# Câmara Municipal de Lisboa

Support for schedules provided by [Câmara Municipal de Lisboa](https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo).

Source for waste collection schedules in Lisboa, Portugal.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cm_lisboa_pt
      args:
        area_name: AREA_NAME
```

### Configuration Variables

**area_name**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cm_lisboa_pt
      args:
        area_name: Restelo
```

## How to get the source arguments

Visit https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo and search for your address on the map. The area name shown in the popup (e.g. 'Restelo', 'Madredeus') is the value to use.
