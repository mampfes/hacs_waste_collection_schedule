# Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis

Support for schedules provided by [Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis](https://www.zva-sek.de).

Source for ZVA (Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zva_sek_de
      args:
        bezirk: BEZIRK
        ortsteil: ORTSTEIL
        strasse: STRASSE
```

### Configuration Variables

**bezirk**  
*(string) (required)*

**ortsteil**  
*(string) (required)*

**strasse**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zva_sek_de
      args:
        bezirk: Fritzlar
        ortsteil: Fritzlar-kernstadt
        strasse: Ahornweg
```
