# LK Schwandorf

LK Schwandorf is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://entsorgung-sad.de> and select your location.  
- Click on `ICS-Datei herunterladen` copy the download link of the downloaded ics file.
- Use this link as the `url` parameter.
- The `regex` is used to extract the pickup date from the event title.

## Examples

### 93133 Hauptstraße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*) \d{2}.\d{2}.\d{4}$
        url: https://entsorgung-sad.de/steuerung/ics.php?plz=93133&ort=Burglengenfeld&ort_ID=4&strasse=Hauptstra%C3%9Fe&rm=202&pt=407&ws=417&spm=0&nr=&zusatz=&email=
```
