# Rudna u Prahy

Support for schedules provided by [Rudna u Prahy](https://www.rudnamesto.cz/).

Source for Rudna u Prahy waste collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mestorudna_cz
      args:
        city_part: CITY_PART
```

### Configuration Variables

**city_part**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mestorudna_cz
      args:
        city_part: "Sud\xE9 t\xFDdny"
```

## How to get the source arguments

Choose your service area from the published map https://www.rudnamesto.cz/odpadovy-kalendar/d-193572. Select whether waste is collected on even or odd weeks.
