# ASTO (Abfall- Sammel- und Transportverband Oberberg)

ASTO (Abfall- Sammel- und Transportverband Oberberg) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.asto.de/> and navigate to the `Abfallkalender` page.
- Click on `Digital / Mobil` in the left navigation sidebar, then select your region in the same sidebar.
- Select your address.
- Right-click -> copy link address on the `Jahreskalender (iCal)` button.
- Paste the copied link into the `url` parameter.
- You can remove the cHash part of the URL, it is not needed.
- It's recommended to replace the year in the URL with `{%Y}` so it will be automatically updated each year if the URL only changes the year.

## Examples

### Marienheide Am Brandteich

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.asto.de/abfallkalender/{%Y}/abfallkalender-jahresdetail/jahrdetail-digital/staedte-listview/district-detailview/district-ical?tx_cctrashcalendar_fetrashcal%5Baction%5D=iCalExport&tx_cctrashcalendar_fetrashcal%5Bcontroller%5D=District&tx_cctrashcalendar_fetrashcal%5Bdistrict%5D=49364
```
