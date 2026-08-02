# Kelkheim (Taunus)

Kelkheim (Taunus) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.kelkheim.de/mod_abfallkalender/> (Persönlicher Abfallkalender).
- Enter your street (`Straße`) and house number (`Hausnummer`). House numbers with a letter suffix (e.g. `9f`) are supported.
- Leave all `Entsorgungsarten` checkboxes checked (or uncheck the ones you don't need) and click `Erstellen`.
- On the results page, click `Link in Zwischenablage kopieren` next to `oder im iCal-Format abonnieren` to copy the iCal link, or right-click the `abonnieren` link and select `copy link`.
- Use this link (starting with `https://`, not `webcal://`) as the `url` parameter.

## Examples

### Rossertstraße 9f

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://kelkheim.de/mod_abfallkalender/index.php?action=ical&area=B-7%2C+S-7+Do&datetype=Restmuell%2CBlaue+Tonne%2CBio-Tonne%2CGelber+Sack%2CSondermuell%2CSperrmuell%2CGruenabfuhr%2CRestmuell-Container%2CGruenschnittannahmestelle%2CWertstoffhof%2CSonstige&street=Rossertstra%DFe&number=9f
```
