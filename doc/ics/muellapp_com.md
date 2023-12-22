# Müll App

Müll App is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to the [Müll App homepage](https://muellapp.com/) and click on "...abonniere den Kalender" or follow [this Link](https://app.muellapp.com/web-reminder?channel=calendar)
- Choose your municipality, address and collection types
- Copy the URL under "Adresse zum Abonnieren" in the "Kalender Abo/Download" tab
- Paste it to the `url` key in the example configuration

## Examples

### Leoben

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://app.muellapp.com/ical/241061?area_filter=174334%2C174336%2C174348%2C187236%2C187237%2C187238%2C187239&reminder
```
