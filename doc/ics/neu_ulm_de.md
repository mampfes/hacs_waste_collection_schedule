# Neu Ulm

Neu Ulm is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://neu-ulm.de/buerger-service/leben-in-neu-ulm/abfall-sauberkeit/abfallkalender> and select your location.  
- Copy the correct link below `Abfuhrtermine als ICS-Dateien`.
- Replace the `url` in the example configuration with this link.
- Replace the year in the url with `{%Y}` so the url should stay valid the next years.
- Keep the regex if you do not want to see the Abfuhr prefix in the event title.
- If you want to split events like `Rest- und Biomüll` into two events, you can use the `split_at` option. ( results in events `Rest` and `Biomüll` You might want to change the name of the first one using the customize option. [_See configuration documentationt_](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/installation.md#configuring-sources).)

## Examples

### Bezirk 3

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: Abfuhr (.*)
        split_at: '- und '
        url: https://nu.neu-ulm.de/securedl/sdl-eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3MDg5MjgxMDAsImV4cCI6MTcwODk3NDkwMCwidXNlciI6MCwiZ3JvdXBzIjpbMCwtMV0sImZpbGUiOiJmaWxlYWRtaW5cL21vdW50XC9zdGFkdC1udVwvcGRmc1wvMl9CdWVyZ2VyX1NlcnZpY2VcL011ZWxsX3VuZF9TYXViZXJrZWl0XC9BYmZhbGxrYWxlbmRlcl9OVV8yMDI0X0Jlemlya18zLmljcyIsInBhZ2UiOjEwODJ9.HbF_Xgiefyjrzr11XCt47CCB0VcpX_TAPsESNncbQZk/Abfallkalender_NU_{%Y}_Bezirk_3.ics
```
