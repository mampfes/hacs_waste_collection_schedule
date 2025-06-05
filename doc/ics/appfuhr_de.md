# Appfuhr.de Ammerland

Appfuhr.de Ammerland is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

['Found this link in the App data, will have to figure out how to get a new one if this ever changes']
## Examples

### Am Röttgen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: ' & '
        url: https://firebasestorage.googleapis.com/v0/b/abfall-ammerland.appspot.com/o/and%2F5%2Fawbapp.json?alt=media
```
