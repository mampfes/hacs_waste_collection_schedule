# WBL Wirtschaftsbetriebe Lünen GmbH

WBL Wirtschaftsbetriebe Lünen GmbH is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://wbl.de/abfallentsorgung/abfuhrtermine-2024> and select your street.
- You may filter the calender by checking "Erweiterte Auswahl" and select only specific bin types. 
- Click on "Abfuhrtermine anzeigen" to generate the specific download-link for your street.
- Right-click on `Terminplaner (iCal, Outlook, Google Kalender, iPhone etc.)` and copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Ackerstrasse

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: ' & '
        url: "https://wbl.de/pdf/ical2024.php?t=1726047592&strasse=Ackerstra\xDFe&no_behaelter_14=0&no_container_14=0&no_behaelter_4=0&no_container_4=0&no_gelb=0&no_gelb_container=0&no_bio=0&no_papier=0&no_papier_container=0"
```
