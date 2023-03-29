# Zweckverband Abfallwirtschaft Kreis Bergstraße

Support for schedules provided by [Zweckverband Abfallwirtschaft Kreis Bergstraße](https://www.zakb.de), serving Kreis Bergstraße, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: zakb_de
      args:
        ort: ORT
        strasse: STRAßE
        hnr: HAUSNUMMER
        hnr_zusatz: HAUSNUMMERZUSATZ
        
```

### Configuration Variables

**ort**  
*(String) (required)*

**strasse**  
*(String) (required)*

**hnr**  
*(String | Integer) (required)*

**hnr_zusatz**  
*(String) (optional)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: zakb_de
      args:
        ort: Abtsteinach
        strasse: Am Hofböhl
        hnr: 1
        hnr_zusatz: 
        
```

## How to get the source argument

Find the parameter of your address using [https://www.zakb.de/online-service/abfallkalender/](https://www.zakb.de/online-service/abfallkalender/) and write them exaclty like on the web page.
