# Mayer Recycling

Mayer Recycling is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.mayer-recycling.at/abfuhrplaene>.
- Right click -> copy link the calendar icon of your Collection region to get the link of the ICS file.
- Use this link as the `url` parameter.

## Examples

### Kalwang

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://58137901-e99c-439f-a523-d74348c63dcf.filesusr.com/ugd/5b01c5_0902fe70c9d2480da3eed6a72fc581fd.ics?dn=Kalender%20von%20Kalwang.ics
```
