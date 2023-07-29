# Kreisstadt Groß-Gerau

Kreisstadt Groß-Gerau is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.gross-gerau.de/B%C3%BCrger-Service-Online-Dienste/Ver-und-Entsorgung/Abfuhrtermine-PDF-Abfallkalender/index.php> and select your street.  
- Click on `Als Kalenderdatei (.ics) herunterladen`, select no alarm. The ICS file will be doanloaded automatically, but one can grab the source URL. (inspecting the button (F12) reveals the URL (you need to add the prefix `https://www.gross-gerau.de`))
- Replace the `url` in the example configuration with this link.

## Examples

### Hagnau

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.gross-gerau.de/output/options.php?ModID=48&call=ical&pois=3411.298&alarm=8
```
