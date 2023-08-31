# Cham Landkreis

Cham Landkreis is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://pwa.entsorgung-cham.de/termine> and select your location.  
- Click on `Termine {YEAR} im Kalender speichern (ICS)` and `Kalenderdaten {YEAR} herunterladen`.
- Copy the download link address.
- Replace the `url` in the example configuration with this link. 
- Replace the year argument with `{%Y}`, so the source will work for all years.
- For easier automations and source configurations you probably want to add the `regex` argument like in the examle below. This will remove the date from the event title.

## Examples

### Arrach, Am Anger

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*) \d{2}\.\d{2}\.\d{4}
        url: https://pwa.entsorgung-cham.de/php/generateICS.php?year={%Y}&plz=93474&ort=Arrach&ort_ID=2&strasse=Am%20Anger&nr=&zusatz=&rm=203&pt=615&ws=206&rm_u=3&pt_u=3&ws_u=3&rmYes=1&ptYes=1&wsYes=1
```
