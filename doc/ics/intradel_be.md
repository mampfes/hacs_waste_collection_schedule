# Intradel (community calendars)

Intradel (community calendars) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Intradel (province of Liège) only publishes its collection calendars as PDF/Issuu documents. The community site <https://intradel-icals.pages.dev> (not official, maintained by a volunteer) converts them into one ICS file per commune and, where applicable, per zone or collection day.
- Go to <https://intradel-icals.pages.dev>, search for your commune and pick the calendar whose collection day matches your address.
- Click `Copier le lien` and use this link as the `url` parameter. The links look like `https://intradel-icals.pages.dev/ics/<commune>.ics` or `https://intradel-icals.pages.dev/ics/<commune>_zone<N>.ics`, e.g. `https://intradel-icals.pages.dev/ics/awans.ics` or `https://intradel-icals.pages.dev/ics/ans_zone2.ics`.
- The calendars only contain the dates of the current calendar year as published by Intradel. They only continue to work if the site is updated with the next year's calendars.

## Examples

### Awans

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://intradel-icals.pages.dev/ics/awans.ics
```
### Ans, zone 2

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://intradel-icals.pages.dev/ics/ans_zone2.ics
```
### Liège, lundi

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://intradel-icals.pages.dev/ics/liege_lundi.ics
```
