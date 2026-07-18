# HubertSchmid Recycling und Umweltschutz GmbH

Support for schedules provided by [HubertSchmid Recycling und Umweltschutz GmbH](https://www.hschmid24.de/BlaueTonne/).

Abfuhrtermine Blaue Tonne

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: api_hubert_schmid_de
      args:
        city: CITY
        ortsteil: ORTSTEIL
        strasse: STRASSE
```

### Configuration Variables

**city**  
*(string) (required)*

**ortsteil**  
*(string) (optional)*

**strasse**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: api_hubert_schmid_de
      args:
        city: Albatsried(Seeg)
```
