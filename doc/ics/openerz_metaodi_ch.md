# Canton of Zürich

Canton of Zürich is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Leave the url as is.
- Set the region to one of the ones listed below.
- Set the zip (not needed for all regions). "The zip code for the collection. Some regions (e.g. Basel) do not provide zip codes." - Website
- Set the area to one of the ones listed below.
- You probably want to leave the regex as is to remove unnecessary information from the summary.

| Region | Areas |
| ------ | ----- |
| adliswil | No Areas |
| basel | A, B, C, D, E, F, G, H |
| bassersdorf | No Areas |
| duebendorf | 1, 2, 3, 4, oekibus-dienstag, oekibus-donnerstag, oekibus-mittwoch, oekibus-montag |
| embrach | ost, west |
| horgen | A, B, C, D |
| kilchberg | A, B |
| langnau | No Areas |
| oberrieden | No Areas |
| richterswil | A, B |
| rueschlikon | A, B |
| stgallen | A, B, C, D, E, F, G, H, I, K, L Ost, L West |
| thalwil | A, B, C |
| uster | 1, 2, 3, 4 |
| waedenswil | A, B, C, D |
| wangen-bruttisellen | No Areas |
| zurich | 8001, 8002, 8003, 8004, 8005, 8006, 8008, 8032, 8037, 8038, 8041, 8044, 8045, 8046, 8047, 8048, 8049, 8050, 8051, 8052, 8053, 8055, 8057, 8064 |

## Examples

### züich 8048

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        params:
          area: 8048
          region: zurich
          zip: 8048
        regex: (.*), .*
        url: https://openerz.metaodi.ch/api/calendar.ics?types=bulky_goods&types=cardboard&types=cargotram&types=chipping_service&types=etram&types=incombustibles&types=metal&types=oekibus&types=organic&types=paper&types=special&types=textile&types=waste&sort=date&offset=0&limit=500
```
### züich 8048 only paper

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        params:
          area: 8048
          region: zurich
          types:
          - cardboard
          - paper
          zip: 8048
        regex: (.*), .*
        url: https://openerz.metaodi.ch/api/calendar.ics?sort=date&offset=0&limit=500
```
### langau everything as types (equal to providing types in the url)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        params:
          region: langnau
          types:
          - bulky_goods
          - cardboard
          - cargotram
          - chipping_service
          - etram
          - incombustibles
          - metal
          - oekibus
          - organic
          - paper
          - special
          - textile
          - waste
          zip: 8135
        regex: (.*), .*
        url: https://openerz.metaodi.ch/api/calendar.ics?sort=date&offset=0&limit=500
```
### waedenswil

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        params:
          area: C
          region: waedenswil
        regex: (.*), .*
        url: https://openerz.metaodi.ch/api/calendar.ics?types=bulky_goods&types=cardboard&types=cargotram&types=chipping_service&types=etram&types=incombustibles&types=metal&types=oekibus&types=organic&types=paper&types=special&types=textile&types=waste&sort=date&offset=0&limit=500
```
