# AbfallNavi (RegioIT.de)

Support for schedules provided by [AbfallNavi (RegioIT.de)](https://www.regioit.de).

Source for AbfallNavi waste collection. AbfallNavi is a brand name of regioit.de.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallnavi_de
      args:
        service: SERVICE
        ort: ORT
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**service**  
*(string) (required)*

**ort**  
*(string) (required)*

**strasse**  
*(string) (optional)*

**hausnummer**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfallnavi_de
      args:
        service: aachen
        ort: Aachen
        strasse: Abteiplatz
        hausnummer: '7'
```

## How to get the source arguments

Pick the 'service' id for your region from the source's list of municipalities, then enter your town ('ort'), and where required the street ('strasse') and house number ('hausnummer').
