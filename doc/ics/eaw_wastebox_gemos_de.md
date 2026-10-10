# EAW Sangerhausen (Gemos)

EAW Sangerhausen (Gemos) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to the EAW waste calendar at <https://eaw.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/> (also embedded at <https://www.abfallwirtschaft-msh.de/index.php/eaw-services-hm/eaw-tup-web-hm>).
- Select your town (`Ort/Ortsteil`) and, if asked, your street. Adjust the waste types and the residual waste rhythm if needed.
- Click `Exportieren iCal` and copy the link shown in the dialog.
- Use this link as the `url` parameter.
- The link contains IDs that change when EAW publishes a new tour plan (usually once a year). The feed then only shows the entry "Es sind neue Abfuhrtermine verfügbar!". Generate a new link and update the `url` when that happens.

## Examples

### Helbra

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://eaw.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/Raw/Name/2026/List/330396/1498,1499,1500,1501,1502,1503,1504,1505,1506/194/Print/ics/Default/Abfuhrtermine.ics
```
### Sangerhausen, Markt

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://eaw.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/Raw/Name/2026/List/331111/1498,1499,1500,1501,1502,1503,1504,1505,1506/194/Print/ics/Default/Abfuhrtermine.ics
```
### Lutherstadt Eisleben, Markt

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://eaw.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/Raw/Name/2026/List/330735/1498,1499,1500,1501,1502,1503,1504,1505,1506/194/Print/ics/Default/Abfuhrtermine.ics
```
