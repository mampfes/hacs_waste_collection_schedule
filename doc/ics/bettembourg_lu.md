# Bettembourg

Bettembourg is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://github.com/knuewelek/beetebuerg-offallkalenner> and click on the 'calendar.ics' file.
- Click on the `Raw` button on the top right side of the code viewer.
- Copy the url (should begin with `https://raw.githubusercontent.com`).
- Replace the `url` in the example configuration with the url you copied.

## Examples

### Bettembourg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://raw.githubusercontent.com/knuewelek/beetebuerg-offallkalenner/refs/heads/main/calendar.ics
```
