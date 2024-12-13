# Südbrandenburgischer Abfallzweckverband, Germany

Support for schedules provided by [SBAZV, Brandenburg, Germany](https://www.sbazv.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sbazv_de
      args:
        url: https://fahrzeuge.sbazv.de/WasteManagementSuedbrandenburg/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=1448170001&AboID=23169&Fra=P;R;WB;L;GS
```

### Configuration Variables

**url**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sbazv_de
      args:
        url: https://fahrzeuge.sbazv.de/WasteManagementSuedbrandenburg/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=1448170001&AboID=23169&Fra=P;R;WB;L;GS
```

## How to get the source arguments

1. Visit the home page of [SBAZV, Germany](https://www.sbazv.de).
2. Click on "Aktuelles" and in the sub menu on "Entsorgungstermine".
3. On the new page that opens click on "Restmüll-/Papiertonne, Gelbe Säcke, Laubsäcke"
4. Choose the waste type and time span
5. Enter your address information (city, street, street number)
6. On the new page that opens click on "Kalenderexport"
7. Click on "URL in die Zwischenablage kopieren" or "URL anzeigen"
8. Copy the URL to the *url* argument of your sensor in home assistant
