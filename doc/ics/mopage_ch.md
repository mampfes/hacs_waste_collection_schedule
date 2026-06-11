# mopage.ch

mopage.ch is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to your municipality's mopage.ch waste calendar page.
- Find the iCal/ICS subscription link (usually a webcal:// URL).
- The generic ICS source automatically converts webcal:// to https://.
- Use the URL as the `url` parameter.

## Examples

### Wiedlisbach

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://wiedlisbach.mopage.ch/appl/ical.php?apid=1366535605&calhome=1341293566
```
