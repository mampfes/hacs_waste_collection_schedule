# Abfallwirtschaft der Stadt St. Pölten

Abfallwirtschaft der Stadt St. Pölten is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.st-poelten.at/sonstiges/17653-abfallkalender> and click "Inhalte von services.st-poelten.at laden"
- fill out your address
- klick F12 or start the dev-mode on your browser another way
- klick on "Download Kalenderexport" and discard or save the file (you'll not need it for that)
- find the link for the ics-file in the "Network"-section of your browsers Dev-tools
- copy the link - for the Landhaus it's https://services.infeo.at/awm/api/st.p%C3%B6lten/wastecalendar/v2/export/?calendarId=135&cityId=162&streetId=124691&housenumber=1&outputType=ical
- (the only values changing here shall be "streetId" and "housenumber")   

## Examples

### Oppach

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: ' & '
        url: https://services.infeo.at/awm/api/st.p%C3%B6lten/wastecalendar/v2/export/?calendarId=135&cityId=162&streetId=124691&housenumber=1&outputType=ical
```
