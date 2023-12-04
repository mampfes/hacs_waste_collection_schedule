# Münsingen BE, Switzerland

Münsingen BE, Switzerland is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to [Abfallkalender](https://www.muensingen.ch/de/verwaltung/dienstleistungen/detail/detail.php?i=90) to get the url of the ICal file.

## Examples

### Papier und Karton

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        title_template: '{{date.summary}} {{date.location}}'
        url: https://www.muensingen.ch/de/verwaltung/dokumente/dokumente/Papier-und-Kartonabfuhr-{%Y}.ics
        version: 1
```
### Gartenabfaelle

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.muensingen.ch/de/verwaltung/dokumente/dokumente/Gartenabfaelle-{%Y}.ics
        version: 1
```
