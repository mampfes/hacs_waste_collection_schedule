# Stadt Koblenz

Stadt Koblenz is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://servicebetrieb.koblenz.de/abfallwirtschaft/entsorgungstermine-digital/>.  
- Right-click on your municipality and copy link address.
- Replace the `url` in the example configuration with this link.
- Replace the year in the url by {%Y}.

## Examples

### Altstadt

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://servicebetrieb.koblenz.de/abfallwirtschaft/entsorgungstermine-digital/entsorgungstermine-2023-digital/altstadt-{%Y}.ics?cid=2ui7
```
