# Abfalltermine Forchheim

Support for schedules provided by [Abfalltermine Forchheim](https://www.abfalltermine-forchheim.de/).

Source for Landkreis Forchheim.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfalltermine_forchheim_de
      args:
        city: CITY
        area: AREA
```

### Configuration Variables

**city**  
*(string) (required)*

**area**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfalltermine_forchheim_de
      args:
        city: Dormitz
        area: Dormitz
```
