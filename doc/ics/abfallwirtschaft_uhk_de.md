# Abfallwirtschaftsbetrieb Unstrut-Hainich-Kreis

Abfallwirtschaftsbetrieb Unstrut-Hainich-Kreis is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.abfallwirtschaft-uhk.de/kopie-tourenpl%C3%A4ne-als-icalendar-f%C3%BCr-das-jahr-2022> and select your municipality (2022 in URL is right!).  
- Right-click on your city/county and copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Altengottern

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://awb-ics.unstrut-hainich-kreis.de/icalendar/2024/Altengottern.ics
```
### Bad Langensalza Stadttour 3

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://awb-ics.unstrut-hainich-kreis.de/icalendar/2024/LST3.ics
```
### Herbsleben

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://awb-ics.unstrut-hainich-kreis.de/icalendar/2024/Herbsleben.ics
```
### Thamsbrück

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://awb-ics.unstrut-hainich-kreis.de/icalendar/2024/Thamsbrueck.ics
```
### Urleben

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://awb-ics.unstrut-hainich-kreis.de/icalendar/2024/Urleben.ics
```
