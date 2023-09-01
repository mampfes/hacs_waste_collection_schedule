# AWIGO

AWIGO is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.awigo.de/> and select your location.  
- Copy the download link of the ICS file (Calendar icon below the big calendar).
- Replace the `url` in the example configuration with this link.
- For easier automations and source configurations you probably want to add the `regex` argument like in the examle below. This will remove " wird abgeholt" event title.

## Examples

### Bippen Alte Ziegelei

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*) wird abgeholt.
        url: https://www.awigo.de/fileadmin/kalender/AWIGO_Kalender_Rest_Papier_Gelb_Bio_Schadstoffmobil_620677001.ics
```
