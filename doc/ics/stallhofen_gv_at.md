# Stallhofen

Stallhofen is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- The ICS calendar is available at <https://www.stallhofen.gv.at/veranstaltungen/kategorie/muellkalender/>.
- Use the URL `https://www.stallhofen.gv.at/veranstaltungen/kategorie/muellkalender/?ical=1&tribe_display=month` as the `url` parameter.

## Examples

### Stallhofen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.stallhofen.gv.at/veranstaltungen/kategorie/muellkalender/?ical=1&tribe_display=month
```
