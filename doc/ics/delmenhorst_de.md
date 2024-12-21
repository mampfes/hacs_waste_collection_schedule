# Abfallkalender Delmenhorst

Abfallkalender Delmenhorst is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.delmenhorst.de/leben/umwelt/abfallentsorgung/abfallkalender.php> 
- Open the pdf file _"Abfuhrbezirke [YYYY] - Straßenverzeichnis mit Zuordnung zur Altpapiertour"_
- Find your street in the pdf and copy the link labeled "iCalendar"
- Replace the `url` in the example configuration with this link.

## Examples

### Delmenhorst Abfuhrbezirk 5 / Altpapiertour B

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.delmenhorst.de/medien/bindata/leben/umwelt-abfall/2025_AB05B.ics
```
### Delmenhorst Abfuhrbezirk 10 / Altpapiertour A

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.delmenhorst.de/medien/bindata/leben/umwelt-abfall/2025_AB10A.ics
```
