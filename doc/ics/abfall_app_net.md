# Abfall App

Abfall App is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto your providers web site collections calendar (alternative https://{service}.abfall-app.net) and select your location.  
- Copy the link of the `Sync zu Kalender` Button.
- Replace the `url` in the example configuration with this link.

known supported:
- Landkreis Stendal: <https://landkreis-stendal.abfall-app.net>
- Landkreis soest: <https://soest.abfall-app.net>
- Landkreis Böblingen: <https://boeblingen.abfall-app.net>
- Altmarkkreis Salzwedel: <https://altmarkkreis-salzwedel.abfall-app.net>
- Landkreis Lüchow-Dannenberg: <https://luechow-dannenberg.abfall-app.net>
- Rhein-Pfalz-Kreis: <https://rhein-pfalz-kreis.abfall-app.net>

## Examples

### Stendal Belkau

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://landkreis-stendal.abfall-app.net/download?system=ical&period=2&district=1321&categories=&view=month
```
### soest

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://soest.abfall-app.net/download?system=ical&period=2&street=24260&categories=&view=month
```
