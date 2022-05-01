# C-Trace.de

Support for schedules provided by [c-trace.de](https://www.c-trace.de).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: c_trace_de
      args:
        ort: ORT
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**ort**<br>
*(string) (required)*

**strasse**<br>
*(string) (required)*

**hausnummer**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: c_trace_de
      args:
        ort: Bremen
        strasse: Abbentorstraße
        hausnummer: 5
```

## How to get the source arguments

Visit the ```Abfallkalender``` page of your city or municipality to get the source arguments:

- [Bremen](https://www.die-bremer-stadtreinigung.de/abfallwirtschaft/entsorgung/bremer-abfallkalender-23080)
