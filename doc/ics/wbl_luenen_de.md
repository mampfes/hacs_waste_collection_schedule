# WBL Lünen

WBL Lünen is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://wbl.de/abfallkalender> and search for your street.
- Copy the ICS download link.
- Replace the year in the URL (e.g. `ical2026.php`) with `ical{%Y}.php`.

## Examples

### Niederadener Straße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://wbl.de/pdf/ical{%Y}.php?strasse=Niederadener+Stra%C3%9Fe
```
