# Stadt Bülach

Stadt Bülach is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.buelach.ch/themen/umwelt-energie-entsorgung/entsorgung/entsorgung-entsorgungskalender>.  
- Right-click -> copy link address on the "Entsorgungskalender" link to get the link to the ICS file.
- Use this url as the `url` argument.

## Examples

### Ost

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://eventfrog.ch/stream/de/eventgroup/6652857603254677856.ics?addId=6663904187270590577
```
