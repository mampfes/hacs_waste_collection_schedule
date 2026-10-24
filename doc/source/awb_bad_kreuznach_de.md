# AWB Bad Kreuznach

Support for schedules provided by [AWB Bad Kreuznach](https://www.awb-kh.de).

Source for AWB Bad Kreuznach.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_bad_kreuznach_de
      args:
        ort: ORT
        stadtteil: STADTTEIL
        strasse: STRASSE
        nummer: NUMMER
```

### Configuration Variables

**ort**  
*(string) (required)*

**stadtteil**  
*(string) (optional)*

**strasse**  
*(string) (optional)*

**nummer**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awb_bad_kreuznach_de
      args:
        ort: Hargesheim
```
