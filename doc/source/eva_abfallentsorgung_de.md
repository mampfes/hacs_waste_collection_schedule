# EVA Abfallentsorgung

EVA Abfallentsorgung

Support for schedules provided by [EVA Abfallentsorgung](https://www.eva-abfallentsorgung.de//), Germany.

## How to get the configuration arguments

- Go to https://www.eva-abfallentsorgung.de/Service-Center/Downloads%20-%20Infos/Abfuhrkalender%20individuell
- Choose Place and Location
- note correct names for ort and strasse

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: eva_abfallentsorgung_de
      args:
        ort: Böbing
        strasse: Böbing
```
or

```yaml
waste_collection_schedule:
  sources:
    - name: eva_abfallentsorgung_de
      args:
        ort: Peißenberg
        strasse: Hauptstraße
```
