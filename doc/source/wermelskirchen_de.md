# Wermelskirchen

Support for schedules provided by [Wermelskirchen](https://www.bavweb.de/Bergischer-Abfallwirtschaftsverband/Abfuhrkalender-Service/Wermelskirchen/).

Source for Abfallabholung Wermelskirchen, Germany

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wermelskirchen_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wermelskirchen_de
      args:
        street: "Telegrafenstra\xDFe"
        house_number: '29'
```
