# Kommunaler Abfallentsorgungsverband Niederlausitz

Support for schedules provided by [kaev.de](https://www.kaev.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kaev_niederlausitz
      args:
        abf_ort: ORT
	abf_ot: ORTSTEIL/GEMEINDETEIL/ORT
        abf_strasse: STRASSE
```

### Configuration Variables

**abf_strasse**<br>
*(string) (required)*

**abf_ort**<br>
*(string) (required)*

**abf_ot**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kaev_niederlausitz
      args:
        abf_strasse: "Zieckau"
        abf_ort: "Luckau"
		abf_ot: "Zieckau"
```

```yaml
waste_collection_schedule:
  sources:
    - name: kaev_niederlausitz
      args:
        abf_strasse: "Bersteweg"
        abf_ort: "Luckau"
		abf_ot: "Luckau"
```


## How to get the source arguments


1. Go to your calendar at `https://www.kaev.de/Info-und-Service/Tourenplan/Tourenplan-Abfalltermine.html`.
2. Enter your location.
