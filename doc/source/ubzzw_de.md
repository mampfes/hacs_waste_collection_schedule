# UBZ Umwelt- und Servicebetrieb Zweibrücken

Support for schedules provided by [UBZ Zweibrücken](https://www.ubzzw.com), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ubzzw_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

Full street name as shown on the UBZ online collection calendar (e.g. `Vogesenstraße`). The spelling must match exactly.

**house_number**  
*(string) (required)*

House number, optionally including a suffix (e.g. `75` or `1 a`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ubzzw_de
      args:
        street: "Vogesenstraße"
        house_number: "75"
```

## How to get the source arguments

1. Go to [https://www.ubzzw.com/servicebereiche/abfall/abfallkalender/](https://www.ubzzw.com/servicebereiche/abfall/abfallkalender/) and click **Zum Online Abfallkalender**.
2. In the popup, select your street's first letter, then your street name, then your house number.
3. Use the street name and house number exactly as they appear in the dropdowns.
