# EVA Abfallentsorgung

EVA Abfallentsorgung is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to https://www.eva-abfallentsorgung.de/Service-Center/Downloads%20-%20Infos/Abfuhrkalender%20individuell
- Choose Place and Location
- Click on `ICS-Datei`
- Turn off Erinnerung
- Right click on `herunterladen` and copy the link address
- Use this link as `url` parameter
- Remove the year argument from the url (may not be necessary)
- You may want to use regex `^(.*) in ` to remove the location from the title (Restmüll<s> In Böbing, Böbing</s>)

## Examples

### Ingenried with regex

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: '^(.*) in '
        split_at: ' & '
        url: https://www.eva-abfallentsorgung.de/genics?ort=Ingenried&strasse=10477&strassenname=Ingenried&erinnerung=0&alarm=0&r=1&b=1&g=1&p=1&s=1
```
### Böbing Without regex

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: ' & '
        url: https://www.eva-abfallentsorgung.de/genics?ort=B%C3%B6bing&strasse=10484&strassenname=B%C3%B6bing&erinnerung=0&alarm=0&r=1&b=1&g=1&p=1&s=1
```
### Eglfing

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.eva-abfallentsorgung.de/genics?ort=Eglfing&strasse=10465&strassenname=Eglfing&erinnerung=0&alarm=0&r=1&b=1&g=1&p=1&s=1&z=1
```
