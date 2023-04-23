# Stadtentsorgung Rostock

Stadtentsorgung Rostock is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.stadtentsorgung-rostock.de/service/ekalend/1216> and select your location.  
- Click on `Abfuhrtermine anzeigen`
- Click on `Jahr`
- Right-click on `Terminexport` and select `Inspect`.
- You should see a HTML fragment like this:

  ```html
  <input class="clear" type="button" name="SubmitIcal" value="iCal" onclick="window.open('/service/ekalend_ical/(key)/GEG~17155-AWI~17155/(period)/year/(type)/rm|lvp|pap|bio','_blank')">
  ```

  The relevant information piece is the text between `(key)/` and `(period)`, which is `GEG~17155-AWI~17155` in this example.

- Replace the corresponding text in the example configuration with your values from the HTML fragment.

## Examples

### Bahnhofstr. 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.stadtentsorgung-rostock.de/service/ekalend_ical/(key)/AWI~156364-GEG~156364/(period)/year
```
### Baumschulenweg 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.stadtentsorgung-rostock.de/service/ekalend_ical/(key)/GEG~17155-AWI~17155/(period)/year
```
