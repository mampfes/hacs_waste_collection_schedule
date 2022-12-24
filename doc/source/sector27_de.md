# Sector27.de

Support for schedules provided by [Sector27.de](https://muellkalender.sector27.de). This service is used by the following cities:

- Datteln
- Marl
- Oer-Erkenschwick

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sector27_de
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
    - name: sector27_de
      args:
        city: Marl
        street: Ahornweg
```
