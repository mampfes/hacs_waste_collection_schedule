# Abfallwirtschaft Rendsburg

Support for schedules provided by [Abfallwirtschaft Rendsburg](https://www.awr.de).

Source for Abfallwirtschaft Rendsburg

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awr_de
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
    - name: awr_de
      args:
        city: Rendsburg
        street: "Hindenburgstra\xDFe"
```
