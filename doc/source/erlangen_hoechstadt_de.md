# Erlangen-Höchstadt

Support for Landkreis Erlangen-Höchstadt located in Bavaria, Germany.

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

**city**  
*(string) (required)*

**street**  
*(string) (required)*

### How to get the source arguments

Visit [erlangen-hoechstadt.de](https://www.erlangen-hoechstadt.de/aktuelles/abfallkalender/) and search for your area. Use the value from the "Ort" dropdown as `city` argument and the matching street from the "Straße auswählen" autocomplete field as `street`. The matching is case-insensitive and matches on substrings (e.g. `street: "Ort inkl. aller Ortsteile"` selects all districts of a municipality).
