# ZAW-SR Straubing

Support for schedules provided by [ZAW-SR](https://www.zaw-sr.de) (Zweckverband Abfallwirtschaft Straubing Stadt und Land), serving the city and district of Straubing, Bavaria, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zaw_sr_de
      args:
        city: Straubing
        street: Theresienplatz
        hnr: "1"
```

### Configuration Variables

**city**
*(string) (required)*

Name of your city or town exactly as shown in the dropdown at [https://www.zaw-sr.de/abfuhrkalender](https://www.zaw-sr.de/abfuhrkalender) (e.g. `Straubing`).

**street**
*(string) (required)*

Your street name exactly as shown in the dropdown (e.g. `Theresienplatz`).

**hnr**
*(string) (required)*

Your house number (e.g. `1`).

**addition**
*(string) (optional, default: `""`)*

Optional house number suffix (e.g. `A`).

## How to get the arguments

1. Open [https://www.zaw-sr.de/abfuhrkalender](https://www.zaw-sr.de/abfuhrkalender).
2. Select your city from the **Ort** dropdown.
3. Select your street from the **Strasse** dropdown.
4. Note the city and street names exactly as they appear — use these as the `city` and `street` arguments.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zaw_sr_de
      args:
        city: Straubing
        street: Stadtgraben
        hnr: "1"
```
