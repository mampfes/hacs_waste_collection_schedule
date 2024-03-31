# Apps by Abfall+

Support for schedules provided by [Hubert Schmid GmbH](https://www.hschmid24.de/BlaueTonne/), serving in Ostallgäu, Bavaria, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: api_hubert_schmid_de
      args:
        city: STADT/KOMMUNE
        ortsteil: ORTSTEIL
        strasse: STRASSE
        
```

### Configuration Variables

**city**  
*(String) (required)*

**strasse**  
*(String) (required)*

**ortsteil**  
*(String) (optional)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: api_hubert_schmid_de
      args:
        city: Füssen
        ortsteil: Eschach
        strasse: Schorrenmoos
```

```yaml
waste_collection_schedule:
    sources:
    - name: api_hubert_schmid_de
      args:
        city: Emmenhausen(Waal)
        strasse: Am Hofanger
```

```yaml
waste_collection_schedule:
    sources:
    - name: app_abfallplus_de
      args:
        app_id: de.k4systems.abfallappwug
        city: Bergen
        strasse: Alle Straßen
```

## How to get the source arguments

Use the website (https://www.hschmid24.de/BlaueTonne/) to find the exact notation of the city, street and optional district.
