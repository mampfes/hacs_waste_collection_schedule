# Heinz-Entsorgung (Landkreis Freising)

Heinz-Entsorgung (Landkreis Freising) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.heinz-entsorgung.de/leistungen/haushalte/entsorgungskalender/entsorgungskalender-freising/> and select your location.
- Click on `ICAL-Datei`
- Select the types of waste you are interested in ("Fraktionen")
- Click on `Ok`
- Download the ics file
- Get the download link address from your browser's download history
- Replace the `url` in the example configuration with this link.

## Examples

### Freising, Am Moosanger (via URL)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.heinz-entsorgung.de/wp-includes/heinz_forms/Abfuhrkalender/php/query.php?ICAL=1&ORT=nRlJXapNmb=c&STRASSE=WQg0WTv92cuF2ZyV&ERINNERUNG=-6&ISERINNERUNG=false&Jahr=2024&FRAKTIONEN=W3siZnJha3Rpb24iOiJSZXN0YWJmYWxsIn0seyJmcmFrdGlvbiI6IkdlbGJlciBTYWNrIn0seyJmcmFrdGlvbiI6IkJpb2FiZmFsbCJ9LHsiZnJha3Rpb24iOiJQYXBpZXIifV0=
```
### Moosburg, Amselstr. (via URL)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.heinz-entsorgung.de/wp-includes/heinz_forms/Abfuhrkalender/php/query.php?ICAL=1&ORT=WTv92c1Jmc=c&STRASSE=WQz1WZzxHduI&ERINNERUNG=-6&ISERINNERUNG=false&Jahr=2024&FRAKTIONEN=W3siZnJha3Rpb24iOiJSZXN0YWJmYWxsIn0seyJmcmFrdGlvbiI6IkdlbGJlciBTYWNrIn0seyJmcmFrdGlvbiI6IkJpb2FiZmFsbCJ9LHsiZnJha3Rpb24iOiJQYXBpZXIifV0=
```
