# ALBA Braunschweig

ALBA Braunschweig is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://alba-bs.de/service/abfuhrtermine.html> and select your location.  
- Copy the link of `ICS-Kalender-Datei` (you may need to click it first and then copy the link from the opened popup)
- Replace the `url` in the example configuration with this link.
- Replace the year in the `url` with `{%Y}`.  
  This will be replaced by the current year.
- You can remove the cHash parameter from the url.

## Examples

### Hauptstrasse 1 C

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://alba-bs.de/service/abfuhrtermine/ajax-kalender.html?tx_mfabfallkalender_mfabfallkalender%5Baction%5D=makeical&tx_mfabfallkalender_mfabfallkalender%5Bcontroller%5D=Abfallkalender&tx_mfabfallkalender_mfabfallkalender%5Bmf-trash-hausnr%5D=1&tx_mfabfallkalender_mfabfallkalender%5Bmf-trash-hausnrzusatz%5D=C&tx_mfabfallkalender_mfabfallkalender%5Bmf-trash-month%5D=6&tx_mfabfallkalender_mfabfallkalender%5Bmf-trash-strasse%5D=Hauptstra%C3%9Fe&tx_mfabfallkalender_mfabfallkalender%5Bmf-trash-thisyear%5D={%Y}
```
