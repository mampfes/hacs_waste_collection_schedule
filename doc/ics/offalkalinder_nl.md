# Ôffalkalinder van Noardeast-Fryslân & Dantumadiel

Ôffalkalinder van Noardeast-Fryslân & Dantumadiel is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://offalkalinder.nl/wanneer> and add your postcode and housenummer.  (9074DL, 1)
- Click on `Zet in agenda`
- Click on `Kopieer naar klembord`
- Replace the `url` in the example configuration with this link.

## Examples

### Oppach

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://offalkalinder.nl/ical/1722200000001856
```
