# Abfallentsorgung Kreis Kassel

Abfallentsorgung Kreis Kassel is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.abfall-kreis-kassel.de/abfallkalender> and select your location.  
- Click on `Dateien und App` expand.
- Click on `ICS - Kalender importieren`
- Right click on `Datei herunterladen` and copy the link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Fuldatal (area 1)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://webapp.abfall-kreis-kassel.de/abfallkalender?no_cache=1&tx_abfallkalender_pi2%5Baction%5D=ical&tx_abfallkalender_pi2%5Bcontroller%5D=Export&cHash=b75e567196581fb1832c0a09b943f2bc&tx_abfallkalender_pi2%5Bcalendar%5D=488&tx_abfallkalender_pi2%5Bfractions%5D=2,6,4,1,7,3,5tx_abfallkalender_pi2%5Breminder%5D=undefined
```
