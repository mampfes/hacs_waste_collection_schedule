# ELW - Entsorgungsbetriebe der Landeshauptstadt Wiesbaden

ELW - Entsorgungsbetriebe der Landeshauptstadt Wiesbaden is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.elw.de/abfallkalender>.
- Within the section "Ihr persönlicher Abfallkalender", enter your address and wait for loading to complete.
- Scroll down to the section with the gray box "Kalender abonnieren als"
- Right click on the link "ical" and copy the link address.

## Examples

### Wilhelm-Dietz-Straße 5

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: ELW - (.*)
        url: https://www.elw.de/fileadmin/elw/php/downloads.php?func=ical&obj=%7B16194D84-3C94-4433-A464-16CEDE63F9F0%7D&location=0
```
