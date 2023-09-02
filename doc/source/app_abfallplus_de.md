# Apps by Abfall+

Support for schedules provided by [Apps by Abfall+](https://www.abfallplus.de/), serving multiple, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: app_abfallplus_de
      args:
        app_id: APP ID
        city: STADT/KOMMUNE
        strasse: STRASSE
        hnr: HAUSNUMMER
        bundesland: BUNDESLAND
        landkreis: LANDKREIS
        
```

### Configuration Variables

**app_id**  
*(String) (required)*

**city**  
*(String) (required)*

**strasse**  
*(String) (required)*

**hnr**  
*(String | Integer) (required)*

**bundesland**  
*(String) (optional)*

**landkreis**  
*(String) (optional)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: app_abfallplus_de
      args:
        app_id: de.albagroup.app
        city: Braunschweig
        strasse: Hauptstraße
        hnr: 7A
        bundesland: 
        landkreis: 
        
```

## How to get the source argument

Find the parameter of your address using []() and write them exactly like on the web page.
