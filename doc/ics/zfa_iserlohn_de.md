# ZfA Iserlohn

ZfA Iserlohn is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.zfa-iserlohn.de/> and select your municipality.
- Click on `Leerungstermine`
- Right-click on `Leerungstermine 20xx als Kaldender-Datei (ICS-Format)` and copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Menden, Bahnstrasse

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.zfa-iserlohn.de/kalender_75e408a534610f9326bd4edd4956abbb.ics
```
### Iserlohn, Bahnhofsplatz

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.zfa-iserlohn.de/kalender_8592ee817bbd0298caa04766b9925484.ics
```
