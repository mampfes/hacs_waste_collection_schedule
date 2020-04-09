# Abfallplus / Abfall IO

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io
      args:
        key: KEY
        kommune: KOMMUNE
        bezirk: BEZIRK
        strasse: strasse
        abfallarten: ABFALLARTEN
```

### Configuration Variables

**key**<br>
*(hash) (required)*

**kommune**<br>
*(integer) (required)*

**bezirk**<br>
*(integer or None) (required)*

**strasse**<br>
*(integer) (required)*

**abfallarten**<br>
*(list(int)) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io
      args:
        key: "8215c62763967916979e0e8566b6172e"
        kommune: 2999
        bezirk: None
        strasse: 1087
        abfallarten: [50, 53, 31, 299, 328, 325]
```
