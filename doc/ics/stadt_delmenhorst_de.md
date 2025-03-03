# Stadt Delmenhorst

Stadt Delmenhorst is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.delmenhorst.de/leben/umwelt/abfallentsorgung/abfallkalender.php> and determine your collection district and the waste paper route.  
- Right-click on `iCalendar <year> Altpapiertour <A or B>` of your collection district and copy link address.
- Replace the `url` in the example configuration with this link. You can replace the year in the URL with "{%Y}" to make it work the next years.
- 

## Examples

### AB01A

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.delmenhorst.de/medien/bindata/leben/umwelt-abfall/{%Y}_AB01A.ics
```
### AB04B

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.delmenhorst.de/medien/bindata/leben/umwelt-abfall/{%Y}_AB04B.ics
```
