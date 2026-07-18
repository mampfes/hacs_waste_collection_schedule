# Städteservice Raunheim Rüsselsheim

Support for schedules provided by [Städteservice Raunheim Rüsselsheim](https://www.staedteservice.de).

Städteservice Raunheim Rüsselsheim

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: staedteservice_de
      args:
        city: CITY
        street_number: STREET_NUMBER
        street_name: STREET_NAME
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street_number**  
*(string) (optional)*

**street_name**  
*(string) (optional)*

**house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: staedteservice_de
      args:
        city: "R\xFCsselsheim"
        street_number: '411'
        house_number: '3'
```
