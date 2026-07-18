# ZKE Saarbrücken

Support for schedules provided by [ZKE Saarbrücken](https://www.zke-sb.de).

Source for Zentraler Kommunaler Entsorgungsbetrieb (ZKE) Saarbrücken.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zke_sb_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zke_sb_de
      args:
        street: Harthweg
        house_number: 7
```
