# Schweinfurt

Support for schedules provided by [Schweinfurt](https://www.schweinfurt.de/leben-freizeit/umwelt/abfallwirtschaft/4427.Aktuelle-Abfuhrtermine-und-Muellkalender.html), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: schweinfurt_de
      args:
        address: ADDRESS
        showmobile: SHOWMOBILE
```

### Configuration Variables

**address**  
*(string) (required)*

**showmobile** (default=false)
*(bool) (optional)*  case-sensitive

## Example


```yaml
waste_collection_schedule:
  sources:
    - name: schweinfurt_de
      args:
        address: "Ahornstrasse"
        showmobile: "True"
```

parameter showmobile is optional
```yaml
waste_collection_schedule:
  sources:
    - name: schweinfurt_de
      args:
        address: "Ahornstrasse"
        showmobile: "False"
```

## How to get the source arguments

1. Go to your calendar at [Schweinfurt - Abfallkalender](https://www.schweinfurt.de/leben-freizeit/umwelt/abfallwirtschaft/4427.Aktuelle-Abfuhrtermine-und-Muellkalender.html)
2. Enter your street and housenumber
3. Copy the exact values from the textboxes street in the source configuration.

Use the showmobile parameter to include schedules for "Mobiler Wertstoffhof"