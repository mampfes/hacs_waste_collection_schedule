# Abfallwirtschaftsbetrieb Esslingen

Support for schedules provided by [Abfallwirtschaftsbetrieb Esslingen](https://www.awb-es.de).

Source for AWB Esslingen, Germany

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_es_de
      args:
        city: CITY
        street: STREET
        restmuell_cadence: RESTMUELL_CADENCE
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (optional)*

**restmuell_cadence**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awb_es_de
      args:
        city: Aichwald
        street: "Alte Dorfstra\xDFe Alle Hausnummern"
```
