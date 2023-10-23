# RecycleCoach

RecycleCoach is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to URL and search for your address.  
- Click "Export Calendar" below the calendar.
- Select all collection types you want to see and in the Choose calendar dropdown, select "iCal".
- Copy the webcal URL from the address bar.
- Replace the `url` in the example configuration with this link.

## Examples

### Asalvegen 1A

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://cal.my-waste.mobi/calendar/getCal?project_id=507&district_id=TownofAurora&info=collection-36-S582-collection-35-S582-collection-34-S581-collection-37-S584&app_nm=webapp&force=1
```
