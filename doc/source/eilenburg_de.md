# Eilenburg

Support for waste collection schedules provided by [Eilenburg](https://www.eilenburg.de), serving Eilenburg (Saxony), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eilenburg_de
      args:
        areas:
        - AREA_1
        - AREA_2
```

### Configuration Variables

**areas**
*(list) (required)*

List of collection areas you want to track. Each address in Eilenburg belongs to one Restmüll/Papier area and one Gelber Sack (yellow bag) area.

**Restmüll and Papier areas:**

| Area name | Description |
|---|---|
| `EB Berg` | Berg district |
| `EB Stadt` | Stadt (city centre) district |
| `EB Ost` | Ost (east) district |
| `EB Ortsteile Dörfer` | Outlying villages |

**Gelber Sack (yellow bag) areas:**

| Area name |
|---|
| `EB 1` |
| `EB 2` |
| `EB 3` |
| `EB 4` |
| `EB 5` |

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: eilenburg_de
      args:
        areas:
        - EB Berg
        - EB 1
```

```yaml
waste_collection_schedule:
    sources:
    - name: eilenburg_de
      args:
        areas:
        - EB Stadt
        - EB 3
```

## How to get the source arguments

Visit [https://www.eilenburg.de/portal/seiten/abfallwirtschaft-900000136-27670.html](https://www.eilenburg.de/portal/seiten/abfallwirtschaft-900000136-27670.html) and download the PDF collection maps to find which area (Entsorgungsbezirk) your address belongs to.

You will typically need one area from the Restmüll/Papier group and one from the Gelber Sack group.
