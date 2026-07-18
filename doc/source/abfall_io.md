# Abfall.IO / AbfallPlus

Support for schedules provided by [Abfall.IO / AbfallPlus](https://www.abfallplus.de).

Source for AbfallPlus.de waste collection. Service is hosted on abfall.io.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io
      args:
        key: KEY
        f_id_kommune: F_ID_KOMMUNE
        f_id_bezirk: F_ID_BEZIRK
        f_id_strasse: F_ID_STRASSE
        f_id_strasse_hnr: F_ID_STRASSE_HNR
        f_abfallarten: F_ABFALLARTEN
```

### Configuration Variables

**key**  
*(string) (required)*

**f_id_kommune**  
*(string) (optional)*

**f_id_bezirk**  
*(string) (optional)*

**f_id_strasse**  
*(string) (optional)*

**f_id_strasse_hnr**  
*(string) (optional)*

**f_abfallarten**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io
      args:
        key: bd0c2d0177a0849a905cded5cb734a6f
        f_id_kommune: 2655
        f_id_bezirk: 2655
        f_id_strasse: 763
```
