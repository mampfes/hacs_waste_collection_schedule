# Valleyfield, Québec

Valleyfield, Québec is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.ville.valleyfield.qc.ca/calendrier-electronique-collecte> and open the IOS tab.  
- Copy the google calendar ICS link of your sector.
- Use this link as the `url` parameter.
- You can use the regex `Collecte (?:du|des) (.*)` to shorten the event titles (will remove the `Collecte du `/`Collecte des ` prefix).

## Examples

### Secteur 3

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: Collecte (?:du|des) (.*)
        url: https://calendar.google.com/calendar/ical/qpsmjqh1odeo11geptq6fp3dis%40group.calendar.google.com/public/basic.ics
```
