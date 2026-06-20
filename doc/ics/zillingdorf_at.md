# Zillingdorf

Zillingdorf is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

The municipality publishes a single public Google Calendar containing all waste collection events.

Use the following URL as the `url` parameter:

`https://calendar.google.com/calendar/ical/v60bh2s8sl7tg2khv1kgg3qu5c%40group.calendar.google.com/public/basic.ics`

## Examples

### Zillingdorf

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://calendar.google.com/calendar/ical/v60bh2s8sl7tg2khv1kgg3qu5c%40group.calendar.google.com/public/basic.ics
```
