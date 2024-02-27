# ART Trier

ART Trier is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.art-trier.de/> and select your municipality.  
- Scroll down to `JAHRESKALENDER FÜR IHR OUTLOOK, ETC.`  
- Set `Wann möchten Sie erinnert werden?` to `Keine Erinnerung` (not mandatory).
- Click on `> Kalender (ICS) importieren` to get a webcal link. Or click on the `ICS-Kalender Speichern` link to download the ics file copy the download link.
- Replace the `url` in the example configuration with this link.

## Examples

### Basberg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*) - .* - A.R.T. Abfuhrtermin
        split_at: ' & '
        url: webcal://art-trier.de/ics-feed/54578:Basberg::@.ics
```
### Trier (Filsch), Edith-Stein-Straße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*) - .* - A.R.T. Abfuhrtermin
        split_at: ' & '
        url: webcal://art-trier.de/ics-feed/54296:Trier:Edith-Stein-Stra%C3%9Fe:Filsch@.ics
```
