# AWB Bad Kreuznach

Support for schedules provided by [AWB Bad Kreuznach](https://abfall-app-bad-kreuznach), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_bad_kreuznach_de
      args:
        ort: ORT
        strasse: STRASSE
        nummer: NUMMER
```

### Configuration Variables

**ort**  
*(string) (required)*

**strasse**  
*(string) (optional)*

**nummer**  
*(string|integer) (optional)*

**stadtteil**  
*(string) (optional)*

`strasse`, `nummer` and `stadtteil` are only needed if the web interface needs them.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awb_bad_kreuznach_de
      args:
        ort: "Hargesheim"
```

```yaml
waste_collection_schedule:
  sources:
    - name: awb_bad_kreuznach_de
      args:
        ort: "Bad Kreuznach"
        strasse: "adalbert-stifter-straße"
        nummer: 3
```

```yaml
waste_collection_schedule:
  sources:
    - name: awb_bad_kreuznach_de
      args:
        ort: "Stromberg"
        stadtteil: "Schindeldorf"
```

## How to get the source arguments

1. Go to your calendar at `https://abfall-app-bad-kreuznach`.
2. Enter your location.
3. Copy the exact values from the select boxes as `stadt`, `stadtteil`, `strasse` and `nummer` in the source configuration (`stadtteil`, `strasse` and `nummer` are only needed for some addresses).

### Old App

1. Go to your calendar at `https://app.awb-bad-kreuznach.de/`.
2. Enter your location.
3. Copy the exact values from the 3 textboxes as `ort`, `strasse` and `nummer` in the source configuration.
