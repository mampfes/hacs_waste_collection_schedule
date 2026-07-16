# Gemeinde Passail

Gemeinde Passail is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.passail.at/muellentsorgung/>.
- Right-click the ICS download link for your collection area and copy the link address.
- Use this link as the `url` parameter.

## Examples

### Passail, Plenzengreith, teilw. Arzberg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://www.passail.at/wp-content/uploads/sites/18/2025/12/Kalender-von-M\xFC\
          lltermine-Passail-Plenzengreith-teilw.-Arzberg.ics"
```
### Hohenau, Neudorf, Rest Arzberg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://www.passail.at/wp-content/uploads/sites/18/2025/12/Kalender-von-M\xFC\
          lltermine-Hohenau-Neudorf-Rest-Arzberg.ics"
```
