# Stadt Wetzlar

Stadt Wetzlar is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://wetzlar.de/leben-in-wetzlar/abfall-und-entsorgung/> and select `Jahreskalender <Jahr>`.
- Search for your `Ortsteil und Straße`.
- Select `Ansicht` and the `Abfallart` you want to see.
- Click `anzeigen`
- Right-click copy link address on the `Jahreskalender als iCal` link to get a ICAL link.
- Use this link as `url` parameter.
- Replace the Year in(`abfuhrtermine-2024`) with `{%Y}` in the URL e.g. `abfuhrtermine-{%Y}`.

## Examples

### Abelsgasse (Wetzlar)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://wetzlar.de/leben-in-wetzlar/abfall-und-entsorgung/abfuhrtermine-{%Y}.php?sp_garbagecalendar_location=Abelsgasse+%28Wetzlar%29&sp_garbagecalendar_view=categoryView&sp_garbagecalendar_garbageTypes%5B%5D=waste&sp_garbagecalendar_garbageTypes%5B%5D=bio&sp_garbagecalendar_garbageTypes%5B%5D=recycle&sp_garbagecalendar_garbageTypes%5B%5D=paper&sp_garbagecalendar_dateSelect_month=11&sp_garbagecalender_icalDownload=true
```
