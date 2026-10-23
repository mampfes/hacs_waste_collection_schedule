# myWasteWatcher (WasteWatcher.NET)

Support for schedules provided by [myWasteWatcher (WasteWatcher.NET)](https://www.mywastewatcher.de).

Source for mywastewatcher.de (WasteWatcher.NET) waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mywastewatcher_de
      args:
        oguid: OGUID
        app_path: APP_PATH
        ort: ORT
        strasse: STRASSE
        ortsteil: ORTSTEIL
        bemerkung: BEMERKUNG
```

### Configuration Variables

**oguid**  
*(string) (optional)*

**app_path**  
*(string) (optional)*

**ort**  
*(string) (optional)*

**strasse**  
*(string) (optional)*

**ortsteil**  
*(string) (optional)*

**bemerkung**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mywastewatcher_de
      args:
        ort: Hamminkeln
        strasse: "Molkereistra\xDFe"
```

## How to get the source arguments

The pre-filled oguid and app_path select Hamminkeln — then just enter city and street exactly as shown on the website. For another municipality, open its calendar page on https://www.mywastewatcher.de (e.g. via the link from your local waste authority): the first path segment of the URL is the app_path (e.g. 'abfallkalenderdk'), and the oguid is the value of the 'oguid' parameter in the URL.
