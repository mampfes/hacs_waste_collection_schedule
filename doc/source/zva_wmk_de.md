# Zweckverband Abfallwirtschaft Werra-Meißner-Kreis

Support für Werra-Meißner-Kreis located in Hesse, Germany

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zva_wmk_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**
*(street) (required)*

### How to get the source arguments

Visit [zva-wmk.de](https://www.zva-wmk.de/termine/schnellsuche-2023) and search for your locality. Use the value from the "Ort" dropdown as `city` argument and the one from "Ortsteil/Straße" as `street` as shown.
