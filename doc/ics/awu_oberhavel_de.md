# Oberhavel AWU

Oberhavel AWU is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.awu-oberhavel.de/fuer-haushalte/zusatzinfos/tourenplan/> and select your location.  
- Right on `Alle Abfallarten` and select copy link.
- Replace the `url` in the example configuration with this link.

## Examples

### Fürstenberg Altthymener Dorfstraße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.awu-oberhavel.de/fuer-haushalte/zusatzinfos/tourenplan/?no_cache=1&export=pap,hm,lvp,bio&city=F%C3%BCrstenberg/Havel%20OT%20Altthymen&street=Altthymener%20Dorfstra%C3%9Fe
```
