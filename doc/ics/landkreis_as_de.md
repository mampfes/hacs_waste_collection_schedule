# Landkreis Amberg-Sulzbach

Landkreis Amberg-Sulzbach is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://landkreis-as.de/abfallwirtschaft/abfuhrtermine.php> and select your location.  
- Click on `Kalenderübersicht anzegen`.
- Right click -> copy link address on the `exportieren` link.
- Replace the `url` in the example configuration with this link.
- You can also use the `regex` to strip unwanted text from the event summary.

## Examples

### Sulzenbach-Rosenberg Am Anger (no regex)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://landkreis-as.de/abfallwirtschaft/abfuhrtermine_kalender_sulzbach-rosenberg8.ics
```
### Freudenberg (regex strip after `|`)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*?)\s+\|.*
        url: https://landkreis-as.de/abfallwirtschaft/abfuhrtermine_kalender_freudenberg.ics
```
### Ensdorf (regex also strip `! vorgefahren !`)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*?)\s+(\||\!).*
        url: https://landkreis-as.de/abfallwirtschaft/abfuhrtermine_kalender_ensdorf.ics
```
