# Apps by Abfall+

Support for schedules provided by [Apps by Abfall+](https://www.abfallplus.de/).

Source for Apps by Abfall+.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: app_abfallplus_de
      args:
        app_id: APP_ID
        bundesland: BUNDESLAND
        landkreis: LANDKREIS
        city: CITY
        bezirk: BEZIRK
        strasse: STRASSE
        hnr: HNR
```

### Configuration Variables

**app_id**  
*(string) (required)*

**bundesland**  
*(string) (optional)*

**landkreis**  
*(string) (optional)*

**city**  
*(string) (optional)*

**bezirk**  
*(string) (optional)*

**strasse**  
*(string) (optional)*

**hnr**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: app_abfallplus_de
      args:
        app_id: de.k4systems.abfallappnf
        city: "Ahrenvi\xF6l"
        strasse: "Alle Stra\xDFen"
```
