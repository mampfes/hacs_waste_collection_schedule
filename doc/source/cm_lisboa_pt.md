# Câmara Municipal de Lisboa

Support for waste collection schedules provided by [Câmara Municipal de Lisboa](https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo).

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

## How to find your area name

Visit the [Dias do Lixo](https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo) page and search for your address on the map. The area name shown in the popup (e.g. "Restelo", "Madredeus", "Campo Ourique") is the value you should use for the `area_name` argument.

## Supported waste types

- **Indiferenciado** — Mixed/undifferentiated waste
- **Papel e Cartão** — Paper and cardboard
- **Embalagens** — Packaging (plastic, metal, carton)
