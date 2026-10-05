# AHE Ennepe-Ruhr-Kreis

Support for schedules provided by [AHE Ennepe-Ruhr-Kreis](https://ahe.de).

Source for AHE Ennepe-Ruhr-Kreis.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ahe_de
      args:
        city: CITY
        bezirk: BEZIRK
        strasse: STRASSE
        hnr: HNR
```

### Configuration Variables

**city**  
*(string) (optional)*

**bezirk**  
*(string) (optional)*

**strasse**  
*(string) (optional)*

**hnr**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ahe_de
      args:
        city: Wetter
        strasse: "Ahornstra\xDFe"
        hnr: Alle Hausnummern
```

## How to get the source arguments

Visit [https://ahe.de/abfallkalender/](https://ahe.de/abfallkalender/) and select your city and street. Use the exact city name as the `city` parameter (e.g. `Wetter`, `Herdecke`, `Gevelsberg`).
