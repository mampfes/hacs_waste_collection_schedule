# StadtService Brühl

Support for schedules provided by [StadtService Brühl](https://stadtservice-bruehl.de).

Source für Abfallkalender StadtService Brühl

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtservice_bruehl_de
      args:
        strasse: STRASSE
        hnr: HNR
```

### Configuration Variables

**strasse**  
*(string) (required)*

**hnr**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadtservice_bruehl_de
      args:
        strasse: "Badorfer Stra\xDFe"
        hnr: '1'
```
