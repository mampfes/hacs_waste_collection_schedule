# Abfall App

Abfall App is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto the AbfallNavi Web site and select iCal-Export. Currently this site is located [here](https://serviceportal.aachen.de/abfallnavi#/schedule).
- Enter your street and house number
- Right-click on the iCal-Export button to copy the link to the iCal file. For the Aachener Straße 11 the link looks like this: https://abfallkalender.regioit.de/kalender-aachen/downloadfile.jsp?format=ics&jahr=2023&ort=Aachen&strasse=10450142&hnr=10450155&fraktion=1&fraktion=4&fraktion=14

Use this link in your configuration. 

## Example

For the example link above the resulting configuration is shown below.

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfallkalender.regioit.de/kalender-aachen/downloadfile.jsp?format=ics&jahr=2023&ort=Aachen&strasse=10450142&hnr=10450155&fraktion=1&fraktion=4&fraktion=14
```
