# AHE Ennepe-Ruhr-Kreis

Support for schedules provided by [AHE Ennepe-Ruhr-Kreis](https://ahe.de), serving Ennepe-Ruhr-Kreis, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ahe_de
      args:
        city: STADT
        strasse: STRAßE
        hnr: HAUSNUMMER
```

### Configuration Variables

**city**
*(String) (required)*

City name. Supported cities: Breckerfeld, Ennepetal, Gevelsberg, Hagen, Hattingen, Herdecke, Schwelm, Sprockhövel, Wetter, Witten.

**strasse**
*(String) (required)*

**hnr**
*(String | Integer) (optional)*

**bezirk**
*(String) (optional)*

Required for some streets that are divided into named districts.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: ahe_de
      args:
        city: Wetter
        strasse: Ahornstraße
        hnr: 1
```

## How to get the source argument

Visit [https://ahe.de/abfallkalender/](https://ahe.de/abfallkalender/) and select your city and street.

> **Migration note (from pre-July 2026 config):** The old `plz` (postal code) parameter is no longer supported. Replace it with `city` (city name, e.g. `Wetter`, `Herdecke`).
