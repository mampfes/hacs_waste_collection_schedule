# Entsorgungsbetrieb Märkisch-Oderland

Entsorgungsbetrieb Märkisch-Oderland is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.entsorgungsbetrieb-mol.de/de/tourenplan-2022.html> and select your location.  
- Click on `Exportieren`.
- Click on `Adresse kopieren` to copy link.
- Replace the `url` in the example configuration with this link.

## Examples

### Buckow, Hasenholz

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://mol.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/Raw/Name/2023/List/585587/2696,2697,2698,2699,2700,2701,2702,2703/Print/ics/Default/Abfuhrtermine.ics
```
