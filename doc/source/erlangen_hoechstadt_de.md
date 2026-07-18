# Landkreis Erlangen-Höchstadt

Support for schedules provided by [Landkreis Erlangen-Höchstadt](https://www.erlangen-hoechstadt.de/).

Source for Landkreis Erlangen-Höchstadt

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

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: erlangen_hoechstadt_de
      args:
        city: "H\xF6chstadt"
        street: "B\xF6hmerwaldstra\xDFe"
```
