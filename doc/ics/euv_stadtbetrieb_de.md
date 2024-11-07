# EUV Stadtbetrieb Castrop-Rauxel

EUV Stadtbetrieb Castrop-Rauxel is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.euv-stadtbetrieb.de/private-haushalte/leerungsabfrage/> and enter your street.    
- Next select your house number
- Click under the section "Google Kalender" on "Link kopieren"
- Replace the `url` in the example configuration with this link.

## Examples

### cas

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://api.euv-stadtbetrieb.de/leerung-ical/v1/385417?link=true
```
