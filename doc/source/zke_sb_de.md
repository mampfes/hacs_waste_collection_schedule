# ZKE Zentraler Kommunaler Entsorgungsbetrieb Saarbrücken

Support for schedules provided by [ZKE Saarbrücken](https://www.zke-sb.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zke_sb_de
      args:
        street: STREET
        house_number: HNR
```

### Configuration Variables

**street**  
_(string) (required)_

**house_number**  
_(string) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zke_sb_de
      args:
        street: "Marieneck"
        house_number: "9 A"
```

## How to get the source arguments

These values are the location you want to query for. Make sure, the writing is exactly as it is on [https://www.zke-sb.de/service/abfuhrtermine/abfuhrkalender](https://www.zke-sb.de/service/abfuhrtermine/abfuhrkalender). Typos may result in an Exception. `house_number` expects a string input **with** address suffixes included.
