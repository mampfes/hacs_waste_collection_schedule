# Rhein-Lahn Kreis

Rhein-Lahn Kreis is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.rhein-lahn-kreis-abfallwirtschaft.de/html/cs_6615.html> and select your location.  
- Rightclick on the link ICS link above the calendar table and copy the liink address.
- Use this url as `url` parameter.
- Replace the year in the `url` with `{%Y}` which will always be replaced with the current year.

## Examples

### Aull

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.rhein-lahn-kreis-abfallwirtschaft.de/abfuhr_export.php?cs=6615&file=ics&gemeinde=3&strasse=&jahr={%Y}
```
### Diez, Auf der Wach

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.rhein-lahn-kreis-abfallwirtschaft.de/abfuhr_export.php?cs=6615&file=ics&gemeinde=7&strasse=211&jahr={%Y}
```
