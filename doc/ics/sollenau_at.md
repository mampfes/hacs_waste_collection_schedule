# Marktgemeinde Sollenau

Marktgemeinde Sollenau is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

The municipality publishes a single public Google Calendar containing all waste collection events (Restmüll, Biomüll, Papier, Gelber Sack, Altkleidersammlung).

Use the following URL as the `url` parameter:

`https://calendar.google.com/calendar/ical/muellsollenau%40gmail.com/public/basic.ics`

## Examples

### Müllplan Sollenau

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://calendar.google.com/calendar/ical/muellsollenau%40gmail.com/public/basic.ics
```
