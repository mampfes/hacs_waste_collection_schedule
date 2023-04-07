# Entsorgungsgesellschaft Görlitz-Löbau-Zittau

Entsorgungsgesellschaft Görlitz-Löbau-Zittau is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.abfall-eglz.de/abfallkalender.html> and select your municipality.  
- Right-click on `Entsorgungstermine als iCalendar herunterladen` and copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Oppach

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.abfall-eglz.de/abfallkalender.html?ort=Oppach&ortsteil=Ort+Oppach&strasse=&ics=1
```
