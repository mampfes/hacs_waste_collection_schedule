# Gemeinde Neuberg

Gemeinde Neuberg is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://neuberg.eu/leben-und-wohnen/abfallkalender>.
- Scroll down to the download section and right-click on the entry titled `Abfallkalender <year>` (the one linking to a file ending in `.ICS`) and copy the link address.
- Use this link as the `url` parameter.

## Examples

### Neuberg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://neuberg.eu/output/download.php?fid=3502.1370.1.ICS
```
