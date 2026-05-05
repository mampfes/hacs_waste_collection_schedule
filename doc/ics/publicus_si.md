# Publicus d.o.o.

Publicus d.o.o. is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://beta.smetar.si/admin/vsiUrniki.php> and search for "Publikus".
- Search for your street and house number.
- Right-click the webcal link and copy the URL.
- Replace `webcal://` with `https://` and use it as the `url` parameter.

## Examples

### Kamnik Na jasi

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://beta.smetar.si/admin/generateICS.php?id=158757
```
