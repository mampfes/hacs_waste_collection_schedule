# Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis (ZVA)

Support for schedules provided by [Abfallwirtschaft Schwalm-Eder-Kreis](https://www.zva-sek.de/) located in Hessia, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zva_sek_de
      args:
        bezirk: BEZITK
        ortsteil: ORTSTEIL
        strasse: STRASSE

```

### Configuration Variables

**bezirk**  
*(string) (required)*

**ortsteil**  
*(string) (required)*

**strasse**  
*(string) (optional) (default: "")*


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zva_sek_de
      args:
        bezirk: "Fritzlar"
        ortsteil: "Fritzlar-kernstadt"
        strasse: "Ahornweg"
```

```yaml
waste_collection_schedule:
  sources:
    - name: zva_sek_de
      args:
        bezirk: "Ottrau"
        ortsteil: "Immichenhain"

```

## How to get the source arguments

These values are the location you want to query for. Make sure, the writing is exactly as it is on [https://www.zva-sek.de/online-dienste](https://www.zva-sek.de/online-dienste) Online-Dienste -> Abfallkalender. Typos will result in an parsing error which is printed in the log.
