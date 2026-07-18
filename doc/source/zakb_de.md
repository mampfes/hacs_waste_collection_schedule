# Zweckverband Abfallwirtschaft Kreis Bergstraße

Support for schedules provided by [Zweckverband Abfallwirtschaft Kreis Bergstraße](https://www.zakb.de).

Source for Zweckverband Abfallwirtschaft Kreis Bergstraße.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zakb_de
      args:
        ort: ORT
        strasse: STRASSE
        hnr: HNR
        hnr_zusatz: HNR_ZUSATZ
```

### Configuration Variables

**ort**  
*(string) (required)*

**strasse**  
*(string) (required)*

**hnr**  
*(string) (required)*

**hnr_zusatz**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zakb_de
      args:
        ort: Abtsteinach
        strasse: "Am Hofb\xF6hl"
        hnr: '1'
        hnr_zusatz: ''
```
