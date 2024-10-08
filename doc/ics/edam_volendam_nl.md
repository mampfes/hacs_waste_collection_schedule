# Edam-Volendam

Edam-Volendam is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.edam-volendam.nl/afvalkalender>.
- Enter your address info and press `Zoeken`.
- Right click and copy the link of the `Bewaar ophaaldagen in uw kalender` button.
- Replace the `url` in the example configuration with this link.

## Examples

### Default

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.edam-volendam.nl/trash-calendar/download/1135AA/1?year
```
