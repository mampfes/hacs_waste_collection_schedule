# Baden Baden

Baden Baden is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.baden-baden.de/buergerservice/umwelt/entsorgung/umweltkalender/> and select your location.  
- Rightclick on the link `iCal Download` link above the calendar table and copy the liink address.
- Use this url as `url` parameter.
- Set Params to `jahr: ""` and year_field to `jahr`.

## Examples

### Neuweier

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        params:
          jahr: ''
        url: https://www.baden-baden.de/buergerservice/umwelt/entsorgung/umweltkalender/?ort=3&strasse=1&abfallart[]=1&abfallart[]=2&abfallart[]=3&abfallart[]=5&abfallart[]=6&abfallart[]=4&t=1&pdf=3
        year_field: jahr
```
