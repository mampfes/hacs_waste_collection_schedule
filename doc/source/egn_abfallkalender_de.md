# EGN Abfallkalender

Support for schedules provided by [EGN Abfallkalender](https://www.egn-abfallkalender.de).

Source for EGN Abfallkalender

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: egn_abfallkalender_de
      args:
        city: CITY
        district: DISTRICT
        street: STREET
        housenumber: HOUSENUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**district**  
*(string) (required)*

**street**  
*(string) (required)*

**housenumber**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: egn_abfallkalender_de
      args:
        city: Dormagen
        district: Hackenbroich
        street: "Aggerstra\xDFe"
        housenumber: 2
```

## How to get the source arguments

Wähle Ort, Ortsteil und Straße wie im EGN-Abfallkalender auf egn-abfallkalender.de und gib die Hausnummer an.
