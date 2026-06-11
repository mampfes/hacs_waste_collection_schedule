# Entsorgungsgesellschaft Görlitz-Löbau-Zittau

Entsorgungsgesellschaft Görlitz-Löbau-Zittau is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.eglz-abfall.de/service/abfallkalender> and select your municipality.
- Right-click on `Entsorgungstermine als iCalendar herunterladen` and copy link address.
- Use this link as the `url` parameter.

## Examples

### Oppach

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.eglz-abfall.de/service/abfallkalender?Ort=Oppach&format=icalc
```
