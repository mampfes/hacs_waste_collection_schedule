# KECL Kommunalentsorgung Chemnitzer Land

KECL Kommunalentsorgung Chemnitzer Land is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.kecl.de/sammeltermine> and select your city by clicking
- Now select your street. You can use the filter on top of the list.
- Copy the link of the `abonnieren` button
- Replace the `url` in the example configuration with this link.

## Examples

### Limbach Oberfrohna Am Hohen Hain

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://www.kecl.de/ical_kalender.php?ort_id=4&strasse_id=601
```
### Zwickau Holunderweg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://www.kecl.de/ical_kalender.php?ort_id=1435&strasse_id=1579
```
