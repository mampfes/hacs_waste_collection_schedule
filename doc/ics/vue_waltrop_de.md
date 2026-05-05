# VUE Waltrop

VUE Waltrop is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.vue-waltrop.de/bereich-abfall/abfallkalender/>.
- Find your district (Bezirk) and right-click the ICS download link.
- Copy the URL and use it as the `url` parameter.

## Examples

### Bezirk 3

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.vue-waltrop.de/wp-content/uploads/2025/11/Bezirk-3.ics
```
