# AWB Bad Kreuznach

Support for schedules provided by [AWB Bad Kreuznach](https://app.awb-bad-kreuznach.de/), Germany.

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

**ort**<br>
*(string) (required)*

**strasse**<br>
*(string) (required)*

**nummer**<br>
*(integer) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awb_bad_kreuznach_de
      args:
        ort: "Hargesheim"
        strasse: "Winzenheimer Straße"
        nummer: 16
```

## How to get the source arguments

1. Go to your calendar at `https://app.awb-bad-kreuznach.de/`.
2. Enter your location.
3. Copy the exact values from the 3 textboxes as `ort`, `strasse` and `nummer` in the source configuration.
