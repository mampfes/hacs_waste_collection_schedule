# UBZ Umwelt- und Servicebetrieb Zweibrücken

Support for schedules provided by [UBZ Umwelt- und Servicebetrieb Zweibrücken](https://www.ubzzw.com).

Source for UBZ Zweibrücken waste collection.

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

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ubzzw_de
      args:
        street: "Vogesenstra\xDFe"
        house_number: '75'
```
