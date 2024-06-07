# Stadt Mainhausen

Stadt Mainhausen is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.mainhausen.de/download-muellkalender> and select your street name.  
- Right-click on `Download Kalenderdatei nur Bezirke mit *selected street name*` and copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Breslauer Straße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.mainhausen.de/municipal/subscribe/trash/15
```
### Aussiger Straße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.mainhausen.de/municipal/subscribe/trash/9
```
### Mainflinger Straße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.mainhausen.de/municipal/subscribe/trash/44
```
