# Landkreis Ravensburg

Support for schedules provided by [Landkreis Ravensburg](https://www.rv.de/), serving Landkreis Ravensburg, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rv_de
      args:
        ort: ORT
        strasse: STRAßE
        hnr: "HAUSNUMMER"
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
*(String | Integer) (optional)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: rv_de
      args:
        ort: Altshausen
        strasse: Altshauser Weg
        hnr: "1"
        hnr_zusatz: 
        
```

## How to get the source argument

Go to [https://www.rv.de/ihr+anliegen/abfall/abfallkalender+-+abfall+app+rv](https://www.rv.de/ihr+anliegen/abfall/abfallkalender+-+abfall+app+rv) click on the link below Abfallkalender zum Ausdrucken.
Find the parameter of your address and write them exactly like on the web page.
