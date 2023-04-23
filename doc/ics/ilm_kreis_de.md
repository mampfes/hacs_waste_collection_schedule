# Abfallwirtschaftsbetrieb Ilm-Kreis

Abfallwirtschaftsbetrieb Ilm-Kreis is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://aik.ilm-kreis.de/Abfuhrtermine/> and select your municipality.  
- Right-click on `Terminexport` and select `Inspect`.
- You should see a HTML fragment like this:

  ```html
  <input class="" style="width:50%;" type="button" title="Termine im Format ICS exportieren" value="Terminexport" data-href="/output/options.php?ModID=48&amp;call=ical&amp;&amp;pois=3053.8&amp;kat=1%2C">
  ```

  The relevant information pieces are the 2 numbers behind `ModID` and `pois` at the end of the HTML fragment:

  ```
  ModID=48
  pois=3053.8
  ```

- Replace the numbers behind `ModID` and `pois` in the example configuration with your values from the HTML fragment.

## Examples

### Oppach

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        headers:
          referer: https://aik.ilm-kreis.de
        url: https://aik.ilm-kreis.de/output/options.php?ModID=48&call=ical&pois=3053.8
```
