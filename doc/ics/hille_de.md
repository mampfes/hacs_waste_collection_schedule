# Gemeinde Hille

Gemeinde Hille is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.hille.de/Wirtschaft-Wohnen/Wohnen/Abfallkalender/>.
- Find the `ICS` download link matching your `Abfuhrbezirk` (collection district). Reminders are not needed for Home Assistant, so the `Ohne Erinnerung` (without reminder) files are recommended.
- Right click the matching link and select `copy link` to get the URL.
- Use this link as the `url` parameter.

## Examples

### Bezirk 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.hille.de/media/custom/3015_1711_1.ICS
```
### Bezirk 2

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.hille.de/media/custom/3015_1712_1.ICS
```
