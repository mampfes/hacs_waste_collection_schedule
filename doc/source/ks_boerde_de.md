# Kommunalservice Landkreis Börde AöR

Support for schedules provided by [Kommunalservice Landkreis Börde AöR](https://ks-boerde.de).

Source for KS Börde.

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

**village**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ks_boerde_de
      args:
        village: Irxleben
        street: "B\xF6rdestra\xDFe"
        house_number: '8'
```
