# Erlangen-Höchstadt
Support for Landkreis [Erlangen-Höchstadt]() located in Bavaria, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: erlangen_hoechstadt_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**<br>
*(string) (required)*

**street**<br>
*(string) (required)*

### How to get the source arguments

Visit [erlangen-hoechstadt.de](https://www.erlangen-hoechstadt.de/aktuelles/abfallkalender/) and search for your area. Use the value from the "Ort" dropdown as `city` argument and the one from "Ortsteil/Straße" as `street`. `street` is case sensitive!