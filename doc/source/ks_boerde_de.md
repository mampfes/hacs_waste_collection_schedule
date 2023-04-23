# Kommunalservice Landkreis Börde AöR

Support for schedules provided by
[Kommunalservice Landkreis Börde AöR](https://ks-boerde.de)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ks_boerde_de
      args:
        village: VILLAGE
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**VILLAGE**  
*(string) (required)*

**STREET**  
*(string) (required)*

**HOUSE_NUMBER**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ks_boerde_de
      args:
        village: Irxleben
        street: Bördestraße
        house_number: 8
```

## How to get the source argument

Use village, street and house number as you would enter them at
https://www.ks-boerde.de/index.php?id=25
