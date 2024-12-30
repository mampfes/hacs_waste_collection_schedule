# Wilnsdorf

Wilnsdorf is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.wilnsdorf.de/Leben-Wohnen/Bauen-Wohnen-Umwelt/Abfall/Abfallkalender/index.php> and select your location.
- Select `Jahreskalender` and your desired waste types.
- Right-click -> `Copy link address` on the `Export in Kalenderanwendung` button.
- Use this URL as the `url` parameter.
- **important**: replace the year in the URL (`vJ=20XX`) with `{%Y}` so it will be automatically updated.
- You might need to set `verify_ssl: False` as there seems to be an issue with the website's SSL certificate.
- Using regex `(.+):.*` will remove the location from the title.

## Examples

### Obersdorf An der Bilze

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.+):.*
        url: https://www.wilnsdorf.de/output/abfall_export.php?csv_export=1&mode=vcal&ort=2678.7&strasse=2678.152.1&abfart%5B0%5D=1.5&abfart%5B1%5D=1.2&abfart%5B2%5D=1.4&abfart%5B3%5D=1.3&abfart%5B4%5D=1.1&abfart%5B5%5D=1.6&vtyp=4&vMo=1&vJ={%Y}&bMo=12
        verify_ssl: false
```
