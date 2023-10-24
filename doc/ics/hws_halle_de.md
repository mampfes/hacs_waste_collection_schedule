# Hallesche Wasser und Stadtwirtschaft GmbH

Hallesche Wasser und Stadtwirtschaft GmbH is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://hws-halle.de/privatkunden/entsorgung-reinigung/behaelterentsorgung/entsorgungskalender> and enter your address.
- Click on `Suchen`
- Right-click on `Termine in Kalender übernehmen` and copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Am Kirchtor 8

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://hws-halle.de/index.php?c=entsorgungskalender&a=generateIcs&str=Am%20Kirchtor&nr=8&kunde1=LEO%201221_H&kunde2=&backend_call=1&year={%Y}
        version: 1
```
### Landrain 129A

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://hws-halle.de/index.php?c=entsorgungskalender&a=generateIcs&str=Landrain&nr=129A&kunde1=LEO%2017314_H&kunde2=&backend_call=1&year={%Y}
        version: 1
```
### Schkopauer Weg 27

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://hws-halle.de/index.php?c=entsorgungskalender&a=generateIcs&str=Schkopauer%20Weg&nr=27&kunde1=LEO%2025674_H&kunde2=&backend_call=1&year={%Y}
        version: 1
```
